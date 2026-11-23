package com.plaintxtoffice.fincalc.ui

import android.annotation.SuppressLint
import android.content.Context
import android.view.Gravity
import android.view.HapticFeedbackConstants
import android.widget.Button
import android.widget.GridLayout

/** Display forms for operator tokens; tokens, saved history, and CSV export stay ASCII. */
object KeyLabels {
    fun format(text: String): String = text.replace('*', '×').replace('/', '÷').replace('-', '−')
}

/** Adding-machine keypad; forwards actions without evaluating expressions. */
// Constructed in Kotlin with required callbacks and theme colors; never inflated from XML.
@SuppressLint("ViewConstructor")
class KeypadView(context: Context, colors: ThemeColors, onKey: (String) -> Unit) : GridLayout(context) {
    init {
        columnCount = 5
        rowCount = 5
        val rows = listOf(
            listOf("log", "(", ")", "C"), listOf("7", "8", "9", "/"),
            listOf("4", "5", "6", "*"), listOf("1", "2", "3", "-"),
            listOf("0", ".", "sign", "+"),
        )
        rows.forEachIndexed { row, keys -> keys.forEachIndexed { col, key ->
            addKey(key, row, col, 1, colors, onKey)
        } }
        addKey("backspace", 0, 4, 1, colors, onKey)
        addKey("^", 1, 4, 1, colors, onKey)
        addKey("=", 2, 4, 3, colors, onKey)
    }

    private companion object {
        val OPERATORS = setOf("/", "*", "-", "+", "^")
        val FUNCTIONS = setOf("C", "backspace", "log", "(", ")")
    }

    private fun addKey(key: String, row: Int, col: Int, span: Int, colors: ThemeColors, onKey: (String) -> Unit) {
        val labels = mapOf("sign" to "±", "backspace" to "⌫")
        val descriptions = mapOf("*" to "Multiply", "/" to "Divide", "-" to "Subtract", "+" to "Add", "sign" to "Change sign",
            "backspace" to "Delete", "C" to "Clear", "=" to "Equals", "^" to "Power", "log" to "Log base 10")
        // Digits read plainest, operators take the accent, and editing keys recede.
        val textColor = when (key) {
            "=" -> colors.background
            in OPERATORS -> colors.accent
            in FUNCTIONS -> colors.muted
            else -> colors.text
        }
        val button = Button(context).apply {
            text = labels[key] ?: KeyLabels.format(key)
            contentDescription = descriptions[key] ?: key
            textSize = if (key in FUNCTIONS) 19f else 24f
            isAllCaps = false
            gravity = Gravity.CENTER
            setPadding(0, 0, 0, 0)
            minimumWidth = 0; minimumHeight = 0
            stateListAnimator = null
            setTextColor(textColor)
            background = context.pressable(if (key == "=") colors.accent else colors.key,
                if (key == "=") colors.background else colors.text)
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
