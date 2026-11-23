package com.plaintxtoffice.fincalc.ui

import android.annotation.SuppressLint
import android.content.Context
import android.content.res.Configuration
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
class CalculatorView(context: Context, colors: ThemeColors, onKey: (String) -> Unit, reuse: (HistoryEntry) -> Unit) : LinearLayout(context) {
    private val tape = TapeView(context, colors, reuse)
    private val empty = TextView(context).apply {
        setText(R.string.history_empty)
        textSize = 15f; gravity = Gravity.CENTER; setTextColor(colors.muted)
        setPadding(context.dp(24), 0, context.dp(24), 0)
    }
    private val display = TextView(context).apply {
        textSize = 44f; gravity = Gravity.END or Gravity.CENTER_VERTICAL
        setTextColor(colors.text); fontFeatureSettings = "tnum"
        minHeight = context.dp(72)
        setPadding(context.dp(12), context.dp(8), context.dp(12), 0)
        setTextIsSelectable(true)
    }
    private val status = TextView(context).apply {
        textSize = 14f; setTextColor(colors.accent); gravity = Gravity.END
        accessibilityLiveRegion = ACCESSIBILITY_LIVE_REGION_POLITE
        minHeight = context.dp(24)
        setPadding(context.dp(12), 0, context.dp(12), context.dp(4))
    }
    init {
        val landscape = resources.configuration.orientation == Configuration.ORIENTATION_LANDSCAPE
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
        controls.addView(display, LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.WRAP_CONTENT))
        controls.addView(status, LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.WRAP_CONTENT))
        controls.addView(KeypadView(context, colors, onKey),
            if (landscape) LayoutParams(LayoutParams.MATCH_PARENT, 0, 1f)
            else LayoutParams(LayoutParams.MATCH_PARENT, context.dp(300)))
    }

    fun render(state: ScreenState) {
        val expression = state.expression.ifEmpty { "0" }
        // Shrink in steps as the expression grows; past the last step the text wraps instead of clipping.
        display.textSize = when {
            expression.length <= 10 -> 44f
            expression.length <= 16 -> 34f
            expression.length <= 24 -> 26f
            else -> 22f
        }
        display.text = KeyLabels.format(expression)
        status.text = state.status
        empty.visibility = if (state.stored.history.isEmpty()) VISIBLE else GONE
        tape.showHistory(state.stored.history, state.stored.settings.decimalPlaces)
    }
}
