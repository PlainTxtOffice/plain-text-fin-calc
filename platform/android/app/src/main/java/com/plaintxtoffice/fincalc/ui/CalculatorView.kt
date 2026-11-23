package com.plaintxtoffice.fincalc.ui

import android.annotation.SuppressLint
import android.content.Context
import android.content.res.Configuration
import android.text.TextPaint
import android.text.TextUtils
import android.util.TypedValue
import android.view.Gravity
import android.widget.FrameLayout
import android.widget.LinearLayout
import android.widget.TextView
import com.plaintxtoffice.fincalc.R
import com.plaintxtoffice.fincalc.application.ScreenState
import com.plaintxtoffice.fincalc.domains.calc.HistoryEntry

/** Render a vertical phone layout or a side-by-side landscape layout. */
// Constructed in Kotlin with required callbacks and theme colors; never inflated from XML.
@SuppressLint("ViewConstructor")
class CalculatorView(
    context: Context, colors: ThemeColors, inputMode: String, onKey: (String) -> Unit, reuse: (HistoryEntry) -> Unit,
) : LinearLayout(context) {
    private val rpn = inputMode == "rpn"
    private val landscape = resources.configuration.orientation == Configuration.ORIENTATION_LANDSCAPE
    /** RPN in phone landscape: the Y line shares the algebraic display height so the keys keep theirs. */
    private val compact = DisplayFit.compact(rpn, landscape, resources.configuration.screenHeightDp)
    private val tape = TapeView(context, colors, reuse)
    private val empty = TextView(context).apply {
        setText(R.string.history_empty)
        textSize = 15f; gravity = Gravity.CENTER; setTextColor(colors.muted)
        setPadding(context.dp(24), 0, context.dp(24), 0)
    }
    /**
     * RPN mode only: the Y register above the main line, which shows X. The line never wraps: a wrapped
     * line limited to one row would show only "Y:", the text of an empty register. A long value shrinks
     * to fit (see [fitYRegister]) and is cut at the start, with an ellipsis, only below the smallest size.
     */
    private val yRegister = TextView(context).apply {
        textSize = DisplayFit.Y_TEXT_SP; gravity = Gravity.END or Gravity.CENTER_VERTICAL
        setTextColor(colors.muted); fontFeatureSettings = "tnum"
        minHeight = context.dp(DisplayFit.Y_HEIGHT_DP)
        isSingleLine = true; ellipsize = TextUtils.TruncateAt.START
        setPadding(context.dp(12), 0, context.dp(12), 0)
        addOnLayoutChangeListener { _, left, _, right, _, oldLeft, _, oldRight, _ ->
            // The size depends on the width, which is unknown until layout; changing it needs a new pass.
            if (right - left != oldRight - oldLeft) post { fitYRegister() }
        }
    }
    private val display = TextView(context).apply {
        textSize = 44f; gravity = Gravity.END or Gravity.CENTER_VERTICAL
        setTextColor(colors.text); fontFeatureSettings = "tnum"
        minHeight = context.dp(DisplayFit.displayMinHeightDp(compact))
        setPadding(context.dp(12), context.dp(DisplayFit.displayTopPaddingDp(compact)), context.dp(12), 0)
        setTextIsSelectable(true)
    }
    private val status = TextView(context).apply {
        textSize = 14f; setTextColor(colors.accent); gravity = Gravity.END
        accessibilityLiveRegion = ACCESSIBILITY_LIVE_REGION_POLITE
        minHeight = context.dp(24)
        setPadding(context.dp(12), 0, context.dp(12), context.dp(4))
    }
    init {
        orientation = if (landscape) HORIZONTAL else VERTICAL
        val history = FrameLayout(context).apply {
            background = context.rounded(colors.surface)
            clipToOutline = true
            addView(tape, FrameLayout.LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.MATCH_PARENT))
            addView(empty, FrameLayout.LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.MATCH_PARENT))
        }
        val controls = LinearLayout(context).apply { orientation = VERTICAL }
        if (landscape) {
            addView(history, LayoutParams(0, LayoutParams.MATCH_PARENT, 1f))
            addView(controls, LayoutParams(0, LayoutParams.MATCH_PARENT, 1.3f).apply { leftMargin = context.dp(8) })
        } else {
            addView(history, LayoutParams(LayoutParams.MATCH_PARENT, 0, 1f))
            addView(controls, LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.WRAP_CONTENT))
        }
        if (rpn) controls.addView(yRegister, LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.WRAP_CONTENT))
        controls.addView(display, LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.WRAP_CONTENT))
        controls.addView(status, LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.WRAP_CONTENT))
        controls.addView(KeypadView(context, colors, inputMode, onKey),
            if (landscape) LayoutParams(LayoutParams.MATCH_PARENT, 0, 1f)
            else LayoutParams(LayoutParams.MATCH_PARENT, context.dp(300)))
    }

    fun render(state: ScreenState) {
        val expression = state.expression.ifEmpty { "0" }
        // Shrink in steps as the expression grows; past the last step the text wraps instead of clipping.
        display.textSize = DisplayFit.displayTextSp(expression.length, compact)
        display.text = KeyLabels.format(expression)
        if (rpn) {
            display.contentDescription = context.getString(R.string.rpn_x_description, display.text)
            val y = state.rpnY?.let(KeyLabels::format)
            yRegister.text = if (y == null) context.getString(R.string.rpn_y_empty) else context.getString(R.string.rpn_y_value, y)
            yRegister.contentDescription = if (y == null) context.getString(R.string.rpn_y_description_empty)
                else context.getString(R.string.rpn_y_description, y)
            fitYRegister()
        }
        status.text = state.status
        empty.visibility = if (state.stored.history.isEmpty()) VISIBLE else GONE
        tape.showHistory(state.stored.history, state.stored.settings.decimalPlaces)
    }

    /** Shrinks the Y line until its text fits the width; the measured width is that of the full size. */
    private fun fitYRegister() {
        val available = yRegister.width - yRegister.paddingLeft - yRegister.paddingRight
        if (available <= 0) return
        val metrics = resources.displayMetrics
        val fullPx = TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_SP, DisplayFit.Y_TEXT_SP, metrics)
        val width = TextPaint(yRegister.paint).apply { textSize = fullPx }.measureText(yRegister.text.toString())
        // Fit in pixels: with a larger system font, sp sizes no longer scale in proportion to each other.
        val fittedPx = DisplayFit.fittedTextSp(width, available.toFloat(), fullPx, DisplayFit.Y_MIN_SCALE)
        if (fittedPx != yRegister.textSize) yRegister.setTextSize(TypedValue.COMPLEX_UNIT_PX, fittedPx)
    }
}
