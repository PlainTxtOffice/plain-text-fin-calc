package com.plaintxtoffice.fincalc.ui

import org.junit.Assert.*
import org.junit.Test

class DisplayFitTest {
    private fun fitted(width: Float, available: Float) =
        DisplayFit.fittedTextSp(width, available, DisplayFit.Y_TEXT_SP, DisplayFit.Y_MIN_SCALE)

    @Test fun yLineKeepsFullSizeWhenTheTextFits() {
        assertEquals(16f, fitted(100f, 272f), 0f)
        assertEquals(16f, fitted(272f, 272f), 0f)
    }

    /** "Y: 0.3333333333333333333333333333" is about 283dp wide at 16sp; a 320dp screen leaves 272dp. */
    @Test fun yLineShrinksUntilAFullPrecisionValueFits() {
        val size = fitted(283f, 272f)
        assertTrue(size < 16f)
        assertTrue(size > 15f)
        // Text width is proportional to its size.
        assertTrue(283f * size / 16f <= 272f)
    }

    @Test fun yLineFitsAtEveryWidthAboveTheSmallestSize() {
        for (width in 273..680) {
            val size = fitted(width.toFloat(), 272f)
            assertTrue("width $width", width * size / 16f <= 272f)
        }
    }

    @Test fun yLineStopsShrinkingAtTheSmallestSize() {
        assertEquals(6.4f, fitted(2000f, 272f), 0.001f)
        assertEquals(6.4f, fitted(100f, 0.5f), 0.001f)
    }

    @Test fun onlyRpnInAShortLandscapeWindowIsCompact() {
        assertTrue(DisplayFit.compact(rpn = true, landscape = true, screenHeightDp = 336))
        assertTrue(DisplayFit.compact(rpn = true, landscape = true, screenHeightDp = 411))
        assertFalse(DisplayFit.compact(rpn = false, landscape = true, screenHeightDp = 336))
        assertFalse(DisplayFit.compact(rpn = true, landscape = false, screenHeightDp = 336))
        assertFalse(DisplayFit.compact(rpn = true, landscape = true, screenHeightDp = 800))
    }

    /** The keypad gets the height that is left, so the lines above it must not grow in phone landscape. */
    @Test fun compactYLineAndDisplayTakeTheAlgebraicDisplayHeight() {
        assertEquals(72, DisplayFit.displayMinHeightDp(compact = false))
        assertEquals(DisplayFit.displayMinHeightDp(compact = false),
            DisplayFit.Y_HEIGHT_DP + DisplayFit.displayMinHeightDp(compact = true))
    }

    /** A line of text with font padding is about 1.33 times its size high in the system font. */
    @Test fun compactDisplayTextFitsItsMinimumHeight() {
        val lineHeightPerSp = 1.33f
        for (length in 0..40) {
            val height = DisplayFit.displayTextSp(length, compact = true) * lineHeightPerSp +
                DisplayFit.displayTopPaddingDp(compact = true)
            assertTrue("length $length", height <= DisplayFit.displayMinHeightDp(compact = true))
        }
        assertTrue(DisplayFit.Y_TEXT_SP * lineHeightPerSp <= DisplayFit.Y_HEIGHT_DP)
    }

    @Test fun displayTextSizesOutsideCompactLayoutsAreUnchanged() {
        assertEquals(44f, DisplayFit.displayTextSp(10, compact = false), 0f)
        assertEquals(34f, DisplayFit.displayTextSp(16, compact = false), 0f)
        assertEquals(26f, DisplayFit.displayTextSp(24, compact = false), 0f)
        assertEquals(22f, DisplayFit.displayTextSp(25, compact = false), 0f)
        assertEquals(8, DisplayFit.displayTopPaddingDp(compact = false))
        assertEquals(34f, DisplayFit.displayTextSp(1, compact = true), 0f)
        assertEquals(22f, DisplayFit.displayTextSp(25, compact = true), 0f)
    }
}
