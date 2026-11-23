package com.plaintxtoffice.fincalc

import com.plaintxtoffice.fincalc.adapters.StoredState
import com.plaintxtoffice.fincalc.application.CalculatorSession
import com.plaintxtoffice.fincalc.config.Settings
import com.plaintxtoffice.fincalc.domains.calc.HistoryEntry
import org.junit.Assert.assertEquals
import org.junit.Test
import java.time.Instant

class HistoryReuseTest {
    private fun entry(result: String) = HistoryEntry(result, result, Instant.EPOCH)

    @Test fun reuseReplacesPreviousAnswer() {
        val session = CalculatorSession(StoredState()) {}
        listOf("2", "*", "3", "=").forEach(session::press)
        val saved = session.state.history.single()
        listOf("1", "+", "1", "=").forEach(session::press)
        val history = session.state.history

        session.reuse(saved)

        assertEquals("6", session.builder.display())
        assertEquals("", session.status)
        assertEquals(history, session.state.history)
    }

    @Test fun reuseReplacesCurrentNumber() {
        listOf("97", "1.25", "-8", "0.").forEach { input ->
            val session = CalculatorSession(StoredState()) {}
            input.forEach { session.press(it.toString()) }

            session.reuse(entry("42"))

            assertEquals("Replacing $input", "42", session.builder.display())
        }
    }

    @Test fun replacementKeepsFullPrecision() {
        val session = CalculatorSession(StoredState(settings = Settings(decimalPlaces = 2))) {}
        listOf("1", "/", "3", "=").forEach(session::press)
        val saved = session.state.history.single()
        listOf("2", "*", "9").forEach(session::press)

        session.reuse(saved)

        assertEquals(listOf("2", "*", saved.result), session.builder.symbols())
        session.press("=")
        assertEquals("0.6666666666666666666666666666", session.state.history.last().result)
    }

    @Test fun repeatedReuseReplacesResult() {
        val session = CalculatorSession(StoredState()) {}
        listOf("-1E-30", "42", "-6.125").forEach { result ->
            session.reuse(entry(result))
            assertEquals(listOf(result), session.builder.symbols())
        }

        listOf("+", "2", "=").forEach(session::press)

        assertEquals("-4.125", session.state.history.last().result)
    }

    @Test fun replacementAllowsFreshDigits() {
        val session = CalculatorSession(StoredState()) {}
        listOf("9", "7").forEach(session::press)
        session.reuse(entry("42"))

        session.press("3")

        assertEquals("3", session.builder.display())
    }

    @Test fun reuseInsideParentheses() {
        val session = CalculatorSession(StoredState()) {}
        listOf("2", "*", "(", "9").forEach(session::press)

        session.reuse(entry("6"))
        session.press(")")

        assertEquals("2 * ( 6 )", session.builder.display())
        session.press("=")
        assertEquals("12", session.state.history.last().result)
    }
}
