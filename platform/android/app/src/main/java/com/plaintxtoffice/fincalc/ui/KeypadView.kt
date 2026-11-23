package com.plaintxtoffice.fincalc.ui

import android.annotation.SuppressLint
import android.content.Context
import android.util.TypedValue
import android.view.Gravity
import android.view.HapticFeedbackConstants
import android.widget.Button
import android.widget.GridLayout
import com.plaintxtoffice.fincalc.R

/** Display forms for operator tokens; tokens, saved history, and CSV export stay ASCII. */
object KeyLabels {
    fun format(text: String): String = text.replace('*', '×').replace('/', '÷').replace('-', '−')
}

/** Adding-machine keypad; forwards actions without evaluating expressions. */
// Constructed in Kotlin with required callbacks and theme colors; never inflated from XML.
@SuppressLint("ViewConstructor")
class KeypadView(context: Context, colors: ThemeColors, inputMode: String, onKey: (String) -> Unit) : GridLayout(context) {
    init {
        columnCount = 5
        rowCount = 5
        // RPN mode has no parentheses or equals: those three positions hold the stack keys.
        val rpn = inputMode == "rpn"
        val rows = listOf(
            if (rpn) listOf("log", "swap", "drop", "C") else listOf("log", "(", ")", "C"), listOf("7", "8", "9", "/"),
            listOf("4", "5", "6", "*"), listOf("1", "2", "3", "-"),
            listOf("0", ".", "sign", "+"),
        )
        rows.forEachIndexed { row, keys -> keys.forEachIndexed { col, key ->
            addKey(key, row, col, 1, colors, onKey)
        } }
        addKey("backspace", 0, 4, 1, colors, onKey)
        addKey("^", 1, 4, 1, colors, onKey)
        addKey(if (rpn) "enter" else "=", 2, 4, 3, colors, onKey)
    }

    private companion object {
        val OPERATORS = setOf("/", "*", "-", "+", "^")
        val FUNCTIONS = setOf("C", "backspace", "log", "(", ")", "swap", "drop")
        val TALL = setOf("=", "enter")
        val WORDS = setOf("enter", "drop")
        const val WORD_SP = 15
        const val WORD_MIN_SP = 6
    }

    private fun addKey(key: String, row: Int, col: Int, span: Int, colors: ThemeColors, onKey: (String) -> Unit) {
        val labels = mapOf("sign" to "±", "backspace" to "⌫", "swap" to context.getString(R.string.key_swap),
            "drop" to context.getString(R.string.key_drop), "enter" to context.getString(R.string.key_enter))
        val descriptions = mapOf("*" to "Multiply", "/" to "Divide", "-" to "Subtract", "+" to "Add", "sign" to "Change sign",
            "backspace" to "Delete", "C" to "Clear", "=" to "Equals", "^" to "Power", "log" to "Log base 10",
            "swap" to context.getString(R.string.key_swap_description), "drop" to context.getString(R.string.key_drop_description),
            "enter" to context.getString(R.string.key_enter_description))
        // Digits read plainest, operators take the accent, and editing keys recede.
        val textColor = when (key) {
            in TALL -> colors.background
            in OPERATORS -> colors.accent
            in FUNCTIONS -> colors.muted
            else -> colors.text
        }
        val button = Button(context).apply {
            text = labels[key] ?: KeyLabels.format(key)
            contentDescription = descriptions[key] ?: key
            textSize = if (key in WORDS) WORD_SP.toFloat() else if (key in FUNCTIONS) 19f else 24f
            maxLines = 1
            // A word is wider than a key at large font sizes; it shrinks to fit instead of being cut mid-word.
            if (key in WORDS) setAutoSizeTextTypeUniformWithConfiguration(WORD_MIN_SP, WORD_SP, 1, TypedValue.COMPLEX_UNIT_SP)
            isAllCaps = false
            gravity = Gravity.CENTER
            setPadding(0, 0, 0, 0)
            minimumWidth = 0; minimumHeight = 0
            stateListAnimator = null
            setTextColor(textColor)
            background = context.pressable(if (key in TALL) colors.accent else colors.key,
                if (key in TALL) colors.background else colors.text)
            setOnClickListener {
                performHapticFeedback(HapticFeedbackConstants.KEYBOARD_TAP)
                onKey(key)
            }
        }
        addView(button, LayoutParams(spec(row, span, span.toFloat()), spec(col, 1f)).apply {
            width = 0; height = 0; setMargins(context.dp(3), context.dp(3), context.dp(3), context.dp(3))
        })
    }
}
