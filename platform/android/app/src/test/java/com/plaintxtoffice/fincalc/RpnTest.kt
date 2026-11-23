package com.plaintxtoffice.fincalc

import com.plaintxtoffice.fincalc.adapters.HistoryExport
import com.plaintxtoffice.fincalc.adapters.StateCodec
import com.plaintxtoffice.fincalc.adapters.StateStore
import com.plaintxtoffice.fincalc.adapters.StoredState
import com.plaintxtoffice.fincalc.application.CalculatorSession
import com.plaintxtoffice.fincalc.config.Settings
import com.plaintxtoffice.fincalc.domains.calc.EvaluationError
import com.plaintxtoffice.fincalc.domains.calc.Evaluator
import com.plaintxtoffice.fincalc.domains.calc.HistoryEntry
import com.plaintxtoffice.fincalc.domains.calc.RpnStack
import com.plaintxtoffice.fincalc.domains.calc.plainResult
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder
import java.io.File
import java.io.IOException
import java.io.StringWriter
import java.time.Instant

/** The shared RPN test vectors V1 to V43 of the behaviour specification, run through the session. */
class RpnTest {
    @get:Rule val temporary = TemporaryFolder()

    /** A session in RPN mode that types vector keys and remembers every tape line it has checked. */
    private class Rpn(places: Int? = null, history: List<HistoryEntry> = emptyList()) {
        val session = CalculatorSession(StoredState(history, Settings(decimalPlaces = places, inputMode = "rpn"))) {}
        val stack get() = session.rpn
        val levels get() = stack.levels
        val entry get() = stack.entry
        val x get() = session.shownExpression().ifEmpty { "0" }
        val y get() = session.shownY()?.let { "Y: $it" } ?: "Y:"
        val tape get() = session.state.history.map { "${it.expression} = ${it.result} | ${it.rpnInput}" }

        /** Vector notation: numbers are typed digit by digit; ENTER, SWAP, DROP, sign, bksp, C, log and operators are keys. */
        fun keys(text: String): Rpn {
            text.split(" ").forEach { token ->
                when (token) {
                    "ENTER", "SWAP", "DROP" -> session.press(token.lowercase())
                    "bksp" -> session.press("backspace")
                    "sign", "C", "log", "+", "-", "*", "/", "^", "." -> session.press(token)
                    else -> token.forEach { session.press(it.toString()) }
                }
            }
            return this
        }

        /** The key is refused with this message and nothing else changes. */
        fun fails(key: String, message: String) {
            val before = stack
            val lines = tape
            val error = assertThrows(EvaluationError::class.java) { keys(key) }
            assertEquals(message, error.message)
            assertEquals(before, stack)
            assertEquals(lines, tape)
        }

        fun reuse(result: String) = session.reuse(HistoryEntry(result, result, Instant.EPOCH))
    }

    private fun state(levels: List<String>, entry: String? = null, lift: Boolean = true, keys: List<String> = emptyList()) =
        RpnStack(levels, entry, lift, keys)

    /** Every tape line must be an expression the algebraic evaluator reproduces exactly. */
    private fun assertTape(rpn: Rpn, vararg lines: String) {
        assertEquals(lines.toList(), rpn.tape)
        rpn.session.state.history.forEach {
            assertEquals(it.expression, it.result, plainResult(Evaluator.evaluate(it.expression.split(" "))))
        }
    }

    @Test fun v01AddShowsRegistersAtEachStep() {
        val rpn = Rpn().keys("3")
        assertEquals(state(emptyList(), "3"), rpn.stack)
        assertEquals("3", rpn.x); assertEquals("Y:", rpn.y)
        rpn.keys("ENTER")
        assertEquals(listOf("3", "3"), rpn.levels); assertFalse(rpn.stack.lift)
        assertEquals("3", rpn.x); assertEquals("Y: 3", rpn.y)
        rpn.keys("4")
        assertEquals(state(listOf("3"), "4", true, listOf("3", "ENTER")), rpn.stack)
        assertEquals("4", rpn.x); assertEquals("Y: 3", rpn.y)
        rpn.keys("+")
        assertEquals(state(listOf("7")), rpn.stack)
        assertEquals("7", rpn.x); assertEquals("Y:", rpn.y)
        assertTape(rpn, "3 + 4 = 7 | 3 ENTER 4 +")
    }

    @Test fun v02DecimalAddition() {
        val rpn = Rpn().keys("0 . 1 ENTER 0 . 2 +")
        assertEquals(listOf("0.3"), rpn.levels)
        assertTape(rpn, "0.1 + 0.2 = 0.3 | 0.1 ENTER 0.2 +")
    }

    @Test fun v03LeadingDecimalPoint() {
        val rpn = Rpn().keys(". 5")
        assertEquals("0.5", rpn.x)
        rpn.keys("ENTER . 2 5")
        assertEquals("0.25", rpn.x)
        rpn.keys("-")
        assertEquals(listOf("0.25"), rpn.levels)
        assertTape(rpn, "0.5 - 0.25 = 0.25 | 0.5 ENTER 0.25 -")
    }

    @Test fun v04ChainedOperations() {
        val rpn = Rpn().keys("3 ENTER 4 + 5")
        assertEquals(state(listOf("7"), "5"), rpn.stack)
        assertEquals("5", rpn.x); assertEquals("Y: 7", rpn.y)
        rpn.keys("*")
        assertEquals(listOf("35"), rpn.levels)
        assertTape(rpn, "3 + 4 = 7 | 3 ENTER 4 +", "7 * 5 = 35 | 5 *")
    }

    @Test fun v05ThreeNumbers() {
        val rpn = Rpn().keys("1 ENTER 2 ENTER 3 +")
        assertEquals(listOf("5", "1"), rpn.levels)
        rpn.keys("+")
        assertEquals(listOf("6"), rpn.levels)
        assertTape(rpn, "2 + 3 = 5 | 1 ENTER 2 ENTER 3 +", "1 + 5 = 6 | +")
    }

    @Test fun v06TwoSumsMultiplied() {
        val rpn = Rpn().keys("2 ENTER 3 + 4 ENTER 5 + *")
        assertEquals(listOf("45"), rpn.levels)
        assertTape(rpn, "2 + 3 = 5 | 2 ENTER 3 +", "4 + 5 = 9 | 4 ENTER 5 +", "5 * 9 = 45 | *")
    }

    @Test fun v07NegativeFirstOperand() {
        val rpn = Rpn().keys("5 sign")
        assertEquals("-5", rpn.entry)
        rpn.keys("ENTER 3 *")
        assertEquals(listOf("-15"), rpn.levels)
        assertTape(rpn, "-5 * 3 = -15 | -5 ENTER 3 *")
    }

    @Test fun v08NegativeSecondOperand() {
        val rpn = Rpn().keys("3 ENTER 5 sign -")
        assertEquals(listOf("8"), rpn.levels)
        assertTape(rpn, "3 - -5 = 8 | 3 ENTER -5 -")
    }

    @Test fun v09SignChangeOfResult() {
        val rpn = Rpn().keys("3 ENTER 4 + sign")
        assertEquals(state(listOf("-7"), keys = listOf("CHS")), rpn.stack)
        assertEquals(1, rpn.tape.size)
        rpn.keys("2 *")
        assertEquals(listOf("-14"), rpn.levels)
        assertTape(rpn, "3 + 4 = 7 | 3 ENTER 4 +", "-7 * 2 = -14 | CHS 2 *")
    }

    @Test fun v10NegativeBasePower() {
        val rpn = Rpn().keys("2 sign ENTER 2 ^")
        assertEquals(listOf("4"), rpn.levels)
        assertTape(rpn, "-2 ^ 2 = 4 | -2 ENTER 2 ^")
    }

    @Test fun v11ThirdTimesThreeKeepsPrecision() {
        assertTape(Rpn().keys("1 ENTER 3 / 3 *"),
            "1 / 3 = 0.3333333333333333333333333333 | 1 ENTER 3 /",
            "0.3333333333333333333333333333 * 3 = 0.9999999999999999999999999999 | 3 *")
    }

    @Test fun v12TwoThirdsRounds() {
        assertTape(Rpn().keys("2 ENTER 3 /"), "2 / 3 = 0.6666666666666666666666666667 | 2 ENTER 3 /")
    }

    @Test fun v13DivisionByZeroChangesNothing() {
        val rpn = Rpn().keys("5 ENTER 0")
        rpn.fails("/", "Division by zero")
        assertEquals(state(listOf("5"), "0", true, listOf("5", "ENTER")), rpn.stack)
        assertEquals("0", rpn.x); assertEquals("Y: 5", rpn.y)
        assertTrue(rpn.tape.isEmpty())
        rpn.keys("bksp")
        assertEquals(state(listOf("5"), keys = listOf("5", "ENTER")), rpn.stack)
        assertEquals("5", rpn.x); assertEquals("Y:", rpn.y)
        rpn.keys("2 /")
        assertEquals(listOf("2.5"), rpn.levels)
        assertTape(rpn, "5 / 2 = 2.5 | 5 ENTER 2 /")
    }

    @Test fun v14EmptyStackKeys() {
        listOf("+", "-", "*", "/", "^", "log", "SWAP", "DROP", "ENTER").forEach { key ->
            val rpn = Rpn()
            rpn.fails(key, "Too few operands")
            assertEquals(RpnStack(), rpn.stack)
        }
        listOf("sign", "bksp", "C").forEach { key ->
            val rpn = Rpn().keys(key)
            assertEquals(RpnStack(), rpn.stack)
            assertEquals("", rpn.session.status)
            assertTrue(rpn.tape.isEmpty())
        }
    }

    @Test fun v15OperatorWithOneNumber() {
        val rpn = Rpn().keys("3")
        rpn.fails("+", "Too few operands")
        assertEquals(state(emptyList(), "3"), rpn.stack)
        assertEquals("3", rpn.x)
        rpn.keys("ENTER +")
        assertEquals(listOf("6"), rpn.levels)
        assertTape(rpn, "3 + 3 = 6 | 3 ENTER +")
    }

    @Test fun v16FullStackRepeatsTop() {
        val rpn = Rpn().keys("4 ENTER ENTER ENTER")
        assertEquals(listOf("4", "4", "4", "4"), rpn.levels); assertFalse(rpn.stack.lift)
        rpn.keys("*")
        assertEquals(listOf("16", "4", "4", "4"), rpn.levels)
        rpn.keys("*")
        assertEquals(listOf("64", "4", "4", "4"), rpn.levels)
        assertTape(rpn, "4 * 4 = 16 | 4 ENTER ENTER ENTER *", "4 * 16 = 64 | *")
    }

    @Test fun v17Swap() {
        val rpn = Rpn().keys("8 ENTER 2 SWAP")
        assertEquals(listOf("8", "2"), rpn.levels)
        rpn.keys("/")
        assertEquals(listOf("0.25"), rpn.levels)
        assertTape(rpn, "2 / 8 = 0.25 | 8 ENTER 2 SWAP /")
    }

    @Test fun v18SwapWithOneNumber() {
        val rpn = Rpn().keys("8")
        rpn.fails("SWAP", "Too few operands")
        assertEquals(state(emptyList(), "8"), rpn.stack)
    }

    @Test fun v19Drop() {
        val rpn = Rpn().keys("1 ENTER 2 ENTER 3 DROP")
        assertEquals(listOf("2", "1"), rpn.levels)
        rpn.keys("+")
        assertEquals(listOf("3"), rpn.levels)
        assertTape(rpn, "1 + 2 = 3 | 1 ENTER 2 ENTER 3 DROP +")
    }

    @Test fun v20DropOnFullStack() {
        val rpn = Rpn().keys("1 ENTER 2 ENTER 3 ENTER 4")
        assertEquals(listOf("3", "2", "1"), rpn.levels); assertEquals("4", rpn.entry)
        rpn.keys("DROP")
        assertEquals(listOf("3", "2", "1", "1"), rpn.levels)
        assertEquals("3", rpn.x); assertEquals("Y: 2", rpn.y)
        rpn.keys("DROP")
        assertEquals(listOf("2", "1", "1", "1"), rpn.levels)
        rpn.keys("DROP")
        assertEquals(listOf("1", "1", "1", "1"), rpn.levels)
        assertTrue(rpn.tape.isEmpty())
        rpn.keys("C")
        assertEquals(RpnStack(), rpn.stack)
    }

    @Test fun v21FifthNumberLosesOldest() {
        val rpn = Rpn().keys("1 ENTER 2 ENTER 3 ENTER 4 ENTER")
        assertEquals(listOf("4", "4", "3", "2"), rpn.levels); assertFalse(rpn.stack.lift)
        rpn.keys("5")
        assertEquals(listOf("4", "3", "2"), rpn.levels); assertEquals("5", rpn.entry)
        rpn.keys("+")
        assertEquals(listOf("9", "3", "2", "2"), rpn.levels)
        rpn.keys("+")
        assertEquals(listOf("12", "2", "2", "2"), rpn.levels)
        rpn.keys("+")
        assertEquals(listOf("14", "2", "2", "2"), rpn.levels)
        assertTape(rpn, "4 + 5 = 9 | 1 ENTER 2 ENTER 3 ENTER 4 ENTER 5 +", "3 + 9 = 12 | +", "2 + 12 = 14 | +")
    }

    @Test fun v22Log() {
        val expected = plainResult(Evaluator.evaluate(listOf("log", "(", "100", ")")))
        assertEquals("2", expected)
        val rpn = Rpn().keys("1 0 0 log")
        assertEquals(state(listOf(expected)), rpn.stack)
        assertTape(rpn, "log ( 100 ) = $expected | 100 LOG")
    }

    @Test fun v23LogOfZero() {
        val rpn = Rpn().keys("0")
        rpn.fails("log", "Log undefined for non-positive values")
        assertEquals("0", rpn.entry)
        assertTrue(rpn.tape.isEmpty())
    }

    @Test fun v24ClearEntryThenClearAll() {
        val rpn = Rpn().keys("3 ENTER 4 C")
        assertEquals(listOf("3"), rpn.levels); assertNull(rpn.entry)
        assertEquals("3", rpn.x); assertEquals("Y:", rpn.y)
        rpn.keys("C")
        assertEquals(RpnStack(), rpn.stack)
        assertEquals("", rpn.session.shownExpression())
        assertEquals("0", rpn.x)
        rpn.fails("+", "Too few operands")
    }

    @Test fun v25Backspace() {
        val rpn = Rpn().keys("1 2")
        assertEquals("12", rpn.entry)
        rpn.keys("bksp")
        assertEquals("1", rpn.entry)
        rpn.keys("3")
        assertEquals("13", rpn.entry)
        rpn.keys("ENTER 2 +")
        assertTape(rpn, "13 + 2 = 15 | 13 ENTER 2 +")
    }

    @Test fun v26SecondDecimalPoint() {
        val rpn = Rpn().keys("1 . 5")
        rpn.fails(".", "Invalid input: .")
        assertEquals("1.5", rpn.entry)
    }

    @Test fun v27EntryDigitLimit() {
        val rpn = Rpn().keys("1234567890123456789012345678")
        rpn.fails("9", "Invalid input: 9")
        assertEquals("1234567890123456789012345678", rpn.entry)
    }

    @Test fun v28NegativeZeroIsZero() {
        val rpn = Rpn().keys("0 sign")
        assertEquals("-0", rpn.entry)
        rpn.keys("ENTER")
        assertEquals(listOf("0", "0"), rpn.levels)
        rpn.keys("5 +")
        assertTape(rpn, "0 + 5 = 5 | 0 ENTER 5 +")
    }

    @Test fun v29ZeroToTheZero() {
        val rpn = Rpn().keys("0 ENTER 0")
        rpn.fails("^", "Invalid exponentiation: 0 ^ 0")
        assertEquals(listOf("0"), rpn.levels); assertEquals("0", rpn.entry)
    }

    @Test fun v30ResultOutOfRange() {
        val rpn = Rpn().keys("9 ENTER 9 9 9 9 9 9 9")
        rpn.fails("^", "Result out of range")
        assertEquals(listOf("9"), rpn.levels); assertEquals("9999999", rpn.entry)
        assertTrue(rpn.tape.isEmpty())
    }

    @Test fun v31ReuseOnFreshStack() {
        val third = "0.3333333333333333333333333333"
        val rpn = Rpn()
        rpn.reuse(third)
        assertEquals(state(listOf(third), keys = listOf(third)), rpn.stack)
        rpn.keys("3 *")
        assertTape(rpn, "$third * 3 = 0.9999999999999999999999999999 | $third 3 *")
    }

    @Test fun v32ReuseAfterResultLiftsStack() {
        val rpn = Rpn().keys("2 ENTER 3 +")
        assertEquals(listOf("5"), rpn.levels)
        rpn.reuse("7")
        assertEquals(listOf("7", "5"), rpn.levels)
        assertEquals("7", rpn.x); assertEquals("Y: 5", rpn.y)
        rpn.keys("*")
        assertTape(rpn, "2 + 3 = 5 | 2 ENTER 3 +", "5 * 7 = 35 | 7 *")
    }

    @Test fun v33ReuseReplacesTypedNumber() {
        val rpn = Rpn().keys("9 7")
        rpn.reuse("42")
        assertNull(rpn.entry); assertEquals(listOf("42"), rpn.levels)
        rpn.keys("3")
        assertEquals("3", rpn.entry); assertEquals(listOf("42"), rpn.levels)
        assertEquals("3", rpn.x); assertEquals("Y: 42", rpn.y)
    }

    @Test fun v34ReuseAfterEnterOverwritesX() {
        val rpn = Rpn().keys("2 ENTER")
        assertEquals(listOf("2", "2"), rpn.levels); assertFalse(rpn.stack.lift)
        rpn.reuse("7")
        assertEquals(listOf("7", "2"), rpn.levels); assertTrue(rpn.stack.lift)
        rpn.keys("+")
        assertTape(rpn, "2 + 7 = 9 | 2 ENTER 7 +")
    }

    @Test fun v35DisplayRoundingKeepsStoredPrecision() {
        val third = "0.3333333333333333333333333333"
        val rpn = Rpn(places = 2).keys("1 ENTER 3 /")
        assertEquals("0.33", rpn.x)
        assertEquals(listOf(third), rpn.levels)
        rpn.keys("3 *")
        assertEquals("1.00", rpn.x)
        val last = rpn.session.state.history.last()
        assertEquals("$third * 3", last.expression)
        assertEquals("0.9999999999999999999999999999", last.result)
        assertTape(rpn, "1 / 3 = $third | 1 ENTER 3 /", "$third * 3 = 0.9999999999999999999999999999 | 3 *")
    }

    @Test fun v36ModeSwitchClearsPendingInputAndKeepsHistory() {
        val rpn = Rpn().keys("1 ENTER 2 + C 3 ENTER 5 ENTER 7")
        assertEquals(listOf("5", "3"), rpn.levels); assertEquals("7", rpn.entry)
        val session = rpn.session
        session.updateSettings(Settings(inputMode = "algebraic"))
        assertEquals("", session.shownExpression())
        assertTrue(session.builder.symbols().isEmpty())
        assertEquals(1, session.state.history.size)
        session.updateSettings(Settings(inputMode = "rpn"))
        assertEquals(RpnStack(), session.rpn)
        assertEquals(1, session.state.history.size)

        val algebraic = CalculatorSession(StoredState()) {}
        listOf("2", "+").forEach(algebraic::press)
        algebraic.updateSettings(Settings(theme = "light"))
        assertEquals("2 +", algebraic.builder.display())
        algebraic.updateSettings(Settings(inputMode = "rpn"))
        assertEquals(RpnStack(), algebraic.rpn)
        assertEquals("", algebraic.shownExpression())
        algebraic.updateSettings(Settings())
        assertEquals("", algebraic.builder.display())

        val same = Rpn().keys("5 ENTER 3")
        same.session.updateSettings(Settings(decimalPlaces = 2, inputMode = "rpn"))
        assertEquals(state(listOf("5"), "3", true, listOf("5", "ENTER")), same.session.rpn)

        assertThrows(IllegalArgumentException::class.java) { same.session.updateSettings(Settings(inputMode = "other")) }
    }

    @Test fun v36FailedSettingsSaveKeepsModeAndInput() {
        val rpn = CalculatorSession(StoredState(settings = Settings(inputMode = "rpn"))) { throw IOException("disk full") }
        listOf("5", "enter", "3").forEach(rpn::press)
        val before = rpn.rpn
        assertThrows(IOException::class.java) { rpn.updateSettings(Settings()) }
        assertEquals("rpn", rpn.state.settings.inputMode)
        assertEquals(before, rpn.rpn)

        val algebraic = CalculatorSession(StoredState()) { throw IOException("disk full") }
        listOf("2", "+").forEach(algebraic::press)
        assertThrows(IOException::class.java) { algebraic.updateSettings(Settings(inputMode = "rpn")) }
        assertEquals("algebraic", algebraic.state.settings.inputMode)
        assertEquals("2 +", algebraic.builder.display())
    }

    @Test fun failedHistorySaveKeepsStackAndHistory() {
        val session = CalculatorSession(StoredState(settings = Settings(inputMode = "rpn"))) { throw IOException("disk full") }
        listOf("3", "enter", "4").forEach(session::press)
        val before = session.rpn
        assertThrows(IOException::class.java) { session.press("+") }
        assertEquals(before, session.rpn)
        assertTrue(session.state.history.isEmpty())
    }

    @Test fun v37ResultsEqualAlgebraicEvaluator() {
        val cases = listOf(
            Triple("0.1", "+", "0.2") to "0.3", Triple("0.3", "-", "0.1") to "0.2",
            Triple("1.1", "*", "1.1") to "1.21", Triple("0.07", "*", "100") to "7",
            Triple("4.35", "*", "100") to "435", Triple("1.005", "*", "1000") to "1005",
            Triple("1", "/", "3") to null, Triple("2", "/", "3") to null,
            Triple("5", "-", "-5") to "10", Triple("-2", "^", "3") to "-8",
            Triple("2", "^", "0.5") to null,
            Triple("1234567890123456789012345678", "-", "1234567890123456789012345677") to "1",
        )
        cases.forEach { (sum, expected) ->
            val (y, operator, x) = sum
            fun typed(number: String) = if (number.startsWith("-")) "${number.drop(1)} sign" else number
            val rpn = Rpn().keys("${typed(y)} ENTER ${typed(x)} $operator")
            val entry = rpn.session.state.history.single()
            val algebraic = plainResult(Evaluator.evaluate(listOf(y, operator, x)))
            assertEquals("$y $operator $x", entry.expression)
            assertEquals(entry.expression, algebraic, entry.result)
            if (expected != null) assertEquals(entry.expression, expected, entry.result)

            // The same sum typed in algebraic mode stores the same result string.
            val session = CalculatorSession(StoredState()) {}
            listOf(y, x).forEachIndexed { index, number ->
                number.removePrefix("-").forEach { session.press(it.toString()) }
                if (number.startsWith("-")) session.press("sign")
                session.press(if (index == 0) operator else "=")
            }
            assertEquals(entry.expression, session.state.history.single().result, entry.result)
        }
    }

    @Test fun v38HistoryAndSettingsStorage() {
        val file = File(temporary.root, "calculator.json")
        val time = Instant.parse("2026-11-23T12:00:05Z")
        val saved = StoredState(listOf(HistoryEntry("1 / 3", "0.3333333333333333333333333333", time),
            HistoryEntry("3 + 4", "7", time, "3 ENTER 4 +")), Settings(inputMode = "rpn"))
        StateStore(file).save(saved)
        assertEquals(saved, StateStore(file).load())
        assertEquals("3 ENTER 4 +", StateStore(file).load().history.last().rpnInput)
        assertEquals("rpn", StateStore(file).load().settings.inputMode)

        // An algebraic entry is written without the key, exactly as before RPN mode existed.
        val algebraic = StateCodec.encode(StoredState(listOf(HistoryEntry("1 + 1", "2", time))))
        assertEquals("""{"settings":{"decimal_places":null,"theme":"dark","max_history_entries":1000,"input_mode":"algebraic"},""" +
            """"history":[{"expression":"1 + 1","result":"2","timestamp":"2026-11-23T12:00:05Z"}]}""", algebraic)
        assertTrue(StateCodec.encode(saved).contains(""""rpn_input":"3 ENTER 4 +""""))

        // A file saved before RPN mode existed loads unchanged.
        val old = """{"settings":{"decimal_places":2,"theme":"light","max_history_entries":50},""" +
            """"history":[{"expression":"1 + 1","result":"2","timestamp":"2026-11-23T12:00:05Z"}]}"""
        assertEquals(StoredState(listOf(HistoryEntry("1 + 1", "2", time)), Settings(2, "light", 50)), StateCodec.decode(old))
        assertNull(StateCodec.decode(old).history.single().rpnInput)

        listOf("5", "\"\"", "null", "[\"3\"]", "true").forEach { value ->
            val text = """{"history":[{"expression":"1 + 1","result":"2","timestamp":"2026-11-23T12:00:05Z","rpn_input":$value},""" +
                """{"expression":"3 + 4","result":"7","timestamp":"2026-11-23T12:00:05Z","rpn_input":"3 ENTER 4 +"}]}"""
            val history = StateCodec.decode(text).history
            assertEquals(value, listOf(null, "3 ENTER 4 +"), history.map { it.rpnInput })
            assertEquals("1 + 1", history.first().expression)
        }

        listOf("""{"settings":{}}""", """{"settings":{"input_mode":7}}""", """{"settings":{"input_mode":"other"}}""",
            """{"settings":{"input_mode":null}}""", """{"settings":{"input_mode":"RPN"}}""", "{}").forEach {
            assertEquals(it, "algebraic", StateCodec.decode(it).settings.inputMode)
        }
        val rpn = StateCodec.decode("""{"settings":{"input_mode":"rpn"}}""")
        assertEquals("rpn", rpn.settings.inputMode)
        assertEquals(rpn, StateCodec.decode(StateCodec.encode(rpn)))
    }

    @Test fun v39CsvHasRpnInputColumn() {
        val entries = listOf(
            HistoryEntry("1 / 3", "0.3333333333333333333333333333", Instant.parse("2026-11-23T12:00:00Z")),
            HistoryEntry("3 + 4", "7", Instant.parse("2026-11-23T12:00:05Z"), "3 ENTER 4 +"),
        )
        val text = StringWriter()
        HistoryExport.write(entries, text)
        assertEquals("timestamp,expression,result,rpn_input\n" +
            "2026-11-23T12:00:00Z,1 / 3,0.3333333333333333333333333333,\n" +
            "2026-11-23T12:00:05Z,3 + 4,7,3 ENTER 4 +\n", text.toString())

        val quoted = StringWriter()
        HistoryExport.write(listOf(entries[1].copy(rpnInput = "a,\"b\"")), quoted)
        assertEquals("timestamp,expression,result,rpn_input\n2026-11-23T12:00:05Z,3 + 4,7,\"a,\"\"b\"\"\"\n", quoted.toString())
    }

    @Test fun csvOfSessionEntries() {
        val rpn = Rpn().keys("3 ENTER 4 +")
        val text = StringWriter()
        HistoryExport.write(rpn.session.state.history, text)
        val timestamp = rpn.session.state.history.single().timestamp
        assertEquals("timestamp,expression,result,rpn_input\n$timestamp,3 + 4,7,3 ENTER 4 +\n", text.toString())
    }

    @Test fun v40KeystrokeLogIsBounded() {
        val rpn = Rpn().keys("1 ENTER")
        repeat(70) { rpn.keys("ENTER") }
        rpn.keys("+")
        val entry = rpn.session.state.history.single()
        assertEquals("1 + 1", entry.expression); assertEquals("2", entry.result)
        val tokens = entry.rpnInput!!.split(" ")
        assertEquals(64, tokens.size)
        assertEquals("...", tokens.first()); assertEquals("+", tokens.last())
        assertEquals(List(62) { "ENTER" }, tokens.subList(1, 63))
    }

    @Test fun v41SavedStateRestore() {
        val rpn = Rpn()
        rpn.session.restoreRpn(listOf("5", "3"), "7", true, listOf("5", "ENTER", "3"))
        assertEquals("7", rpn.x); assertEquals("Y: 5", rpn.y)
        rpn.keys("+")
        assertTape(rpn, "5 + 7 = 12 | 5 ENTER 3 7 +")
        assertEquals(listOf("12", "3"), rpn.levels)

        val invalid = listOf(
            RpnStack.restore(listOf("abc"), null, true, emptyList()),
            RpnStack.restore(listOf("1", "2", "3", "4", "5"), null, true, emptyList()),
            RpnStack.restore(listOf("5", "5"), "7", false, emptyList()),
            RpnStack.restore(listOf("5"), null, false, emptyList()),
            RpnStack.restore(listOf("5", "3"), null, false, emptyList()),
            RpnStack.restore(listOf("5"), "1.2.3", true, emptyList()),
            RpnStack.restore(listOf("5"), "-", true, emptyList()),
            RpnStack.restore(listOf("5"), "12345678901234567890123456789", true, emptyList()),
            RpnStack.restore(listOf("5"), null, true, listOf("5", "PRESS")),
            RpnStack.restore(listOf("5"), null, true, List(65) { "ENTER" }),
        )
        invalid.forEachIndexed { index, stack -> assertEquals("case $index", RpnStack(), stack) }

        assertEquals(state(listOf("1.5", "1.5", "0"), null, false, listOf("...", "1.5", "ENTER")),
            RpnStack.restore(listOf("1.50", "1.5", "-0"), "", false, listOf("...", "1.5", "ENTER")))

        val algebraic = CalculatorSession(StoredState()) {}
        algebraic.restoreRpn(listOf("5", "3"), "7", true, listOf("5", "ENTER", "3"))
        assertEquals(RpnStack(), algebraic.rpn)
        algebraic.restore(listOf("2", "+"), false)
        assertEquals("2 +", algebraic.builder.display())

        // In RPN mode saved algebraic tokens are ignored.
        rpn.session.restore(listOf("2", "+"), false)
        assertTrue(rpn.session.builder.symbols().isEmpty())
    }

    @Test fun v42LiftAfterKeysOtherThanEnter() {
        val rpn = Rpn().keys("5 ENTER sign")
        assertEquals(state(listOf("-5", "5"), null, true, listOf("5", "ENTER", "CHS")), rpn.stack)
        rpn.keys("3")
        assertEquals(listOf("-5", "5"), rpn.levels); assertEquals("3", rpn.entry)
        assertEquals("Y: -5", rpn.y)

        val cleared = Rpn().keys("0 ENTER C")
        assertEquals(RpnStack(), cleared.stack)
        cleared.keys("sign")
        assertEquals(RpnStack(), cleared.stack)

        val twice = Rpn().keys("7 ENTER sign sign")
        assertEquals(listOf("7", "7"), twice.levels); assertTrue(twice.stack.lift)
    }

    @Test fun v43CancelledEntry() {
        val rpn = Rpn().keys("5 ENTER 3 bksp")
        assertEquals(listOf("5"), rpn.levels); assertNull(rpn.entry); assertTrue(rpn.stack.lift)
        rpn.fails("+", "Too few operands")
        rpn.keys("ENTER +")
        assertTape(rpn, "5 + 5 = 10 | 5 ENTER ENTER +")
    }

    @Test fun canonAndZeroText() {
        listOf("0", "-0", "0.", "-0.00", "000").forEach { assertTrue(it, RpnStack.isZeroText(it)) }
        listOf("", "-", ".", "1", "0.1", "0..", "--0", "0-").forEach { assertFalse(it, RpnStack.isZeroText(it)) }
        mapOf("0." to "0", "-0" to "0", "1.50" to "1.5", "007" to "7", "-5" to "-5", "5." to "5").forEach { (text, expected) ->
            assertEquals(text, expected, RpnStack.canon(text))
        }
        assertEquals("Invalid number: abc", assertThrows(EvaluationError::class.java) { RpnStack.canon("abc") }.message)
    }

    @Test fun equalsKeyAndParenthesesInRpnMode() {
        val rpn = Rpn().keys("3")
        rpn.session.press("=")
        assertEquals(listOf("3", "3"), rpn.levels); assertFalse(rpn.stack.lift)
        rpn.fails("(", "Invalid input: (")
        rpn.fails(")", "Invalid input: )")
    }

    @Test fun everyKeyClearsStatusAndReuseErrorsChangeNothing() {
        val rpn = Rpn().keys("9 7")
        val before = rpn.stack
        val error = assertThrows(EvaluationError::class.java) { rpn.reuse("abc") }
        assertEquals("Invalid number: abc", error.message)
        assertEquals(before, rpn.stack)
        assertEquals("", rpn.session.status)
    }

    @Test fun signOfZeroInXStaysZero() {
        val rpn = Rpn().keys("0 ENTER 5 - 5 + sign")
        assertEquals(listOf("0"), rpn.levels)
        assertEquals(listOf("CHS"), rpn.stack.keys)
    }

    @Test fun rpnEntriesObeyHistoryCap() {
        val session = CalculatorSession(StoredState(settings = Settings(maxHistoryEntries = 2, inputMode = "rpn"))) {}
        listOf("1", "enter", "enter", "enter", "+", "+", "+").forEach(session::press)
        assertEquals(listOf("3", "4"), session.state.history.map { it.result })
    }
}
