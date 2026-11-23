package com.plaintxtoffice.fincalc.ui

import kotlin.math.floor

/** Size rules for the display lines, kept as plain arithmetic so local tests can check them without a device. */
object DisplayFit {
    /** Full text size of the RPN Y register line. */
    const val Y_TEXT_SP = 16f
    /** The Y line shrinks to this share of its full size before it is truncated at the start. */
    const val Y_MIN_SCALE = 0.4f
    const val Y_HEIGHT_DP = 24
    const val DISPLAY_HEIGHT_DP = 72
    private const val DISPLAY_TOP_PADDING_DP = 8
    private const val COMPACT_TEXT_SP = 34f
    /** Landscape windows lower than this are phones, where every dp above the keypad shortens the keys. */
    private const val SHORT_WINDOW_DP = 480
    private const val SIZE_STEPS_PER_SP = 4

    /**
     * True when the Y line has to share the height of the algebraic display instead of adding to it:
     * RPN mode in a short landscape window, where the keypad gets whatever height is left.
     */
    fun compact(rpn: Boolean, landscape: Boolean, screenHeightDp: Int): Boolean =
        rpn && landscape && screenHeightDp < SHORT_WINDOW_DP

    /** Minimum height of the main display line; in compact layouts the Y line takes its share. */
    fun displayMinHeightDp(compact: Boolean): Int = if (compact) DISPLAY_HEIGHT_DP - Y_HEIGHT_DP else DISPLAY_HEIGHT_DP

    /** The Y line directly above already separates a compact display from the title bar. */
    fun displayTopPaddingDp(compact: Boolean): Int = if (compact) 0 else DISPLAY_TOP_PADDING_DP

    /** Main display text size: smaller in steps as the text grows, and capped where the line is lower. */
    fun displayTextSp(length: Int, compact: Boolean): Float {
        val size = when {
            length <= 10 -> 44f
            length <= 16 -> 34f
            length <= 24 -> 26f
            else -> 22f
        }
        return if (compact) minOf(size, COMPACT_TEXT_SP) else size
    }

    /**
     * Text size at which a single line fits [available] pixels, given its width [widthAtFull] at [fullSp].
     * Never below [minScale] of the full size; text that is still too wide is truncated by the view.
     */
    fun fittedTextSp(widthAtFull: Float, available: Float, fullSp: Float, minScale: Float): Float {
        if (widthAtFull <= available) return fullSp
        // Round down to a quarter sp so the rounded size cannot be wider than the line.
        val fitted = floor(fullSp * available / widthAtFull * SIZE_STEPS_PER_SP) / SIZE_STEPS_PER_SP
        return maxOf(fullSp * minScale, fitted)
    }
}
