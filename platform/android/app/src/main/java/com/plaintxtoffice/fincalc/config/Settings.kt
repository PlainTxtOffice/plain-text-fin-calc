package com.plaintxtoffice.fincalc.config

/**
 * User preferences; null precision/cap means full precision/unlimited history. [inputMode] is
 * "algebraic" or "rpn".
 */
data class Settings(
    val decimalPlaces: Int? = null,
    val theme: String = "dark",
    val maxHistoryEntries: Int? = 1000,
    val inputMode: String = "algebraic",
)
