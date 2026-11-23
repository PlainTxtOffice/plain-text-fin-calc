package com.plaintxtoffice.fincalc.application

import com.plaintxtoffice.fincalc.adapters.StoredState
import com.plaintxtoffice.fincalc.config.Settings
import com.plaintxtoffice.fincalc.domains.calc.*
import java.time.Instant

/** Coordinate input and persistence; failed writes leave history and preferences unchanged. */
class CalculatorSession(initial: StoredState, private val save: (StoredState) -> Unit) {
    val builder = ExpressionBuilder()
    /** The RPN stack; stays empty in algebraic mode. It lives in saved UI state, not in the stored file. */
    var rpn = RpnStack()
        private set
    var state = initial.copy(history = trimHistory(initial.history, initial.settings.maxHistoryEntries))
        private set
    var status = ""
        private set

    fun press(key: String) {
        status = ""
        if (isRpn) return apply(rpn.press(if (key == "=") "enter" else key))
        when (key) {
            "C" -> builder.clear()
            "backspace" -> builder.backspace()
            "sign" -> builder.toggleSign()
            "=" -> calculate()
            else -> if (!builder.add(key)) status = "Invalid input: $key"
        }
    }

    private fun calculate() {
        if (builder.symbols().isEmpty()) return
        val result = plainResult(Evaluator.evaluate(builder.symbols()))
        val entry = HistoryEntry(builder.display(), result, Instant.now())
        commit(state.copy(history = trimHistory(state.history + entry, state.settings.maxHistoryEntries)))
        builder.clear()
        builder.insertResult(result)
    }

    private val isRpn get() = state.settings.inputMode == "rpn"

    /** Save the tape line of a calculating key before the stack changes, so a failed save changes nothing. */
    private fun apply(step: RpnStep) {
        step.record?.let {
            val entry = HistoryEntry(it.expression, it.result, Instant.now(), it.rpnInput)
            commit(state.copy(history = trimHistory(state.history + entry, state.settings.maxHistoryEntries)))
        }
        rpn = step.stack
    }

    /** The text of the main display line: the expression, or the X register in RPN mode. */
    fun shownExpression(): String {
        val places = state.settings.decimalPlaces
        if (isRpn) return rpn.entry ?: rpn.levels.firstOrNull()?.let { formatResult(it, places) }.orEmpty()
        return if (builder.hasPendingResult() && builder.symbols().size == 1) formatResult(builder.symbols().single(), places)
            else builder.display()
    }

    /** The Y register as shown in RPN mode, or null when it is empty or the mode is algebraic. */
    fun shownY(): String? = if (isRpn) rpn.visibleY?.let { formatResult(it, state.settings.decimalPlaces) } else null

    /** Restore unfinished algebraic input from saved UI state; ignored in RPN mode. */
    fun restore(tokens: List<String>, pending: Boolean) { if (!isRpn) builder.restore(tokens, pending) }

    /** Restore the stack from saved UI state; ignored in algebraic mode, empty if anything is invalid. */
    fun restoreRpn(levels: List<String>, entry: String, lift: Boolean, keys: List<String>) {
        if (isRpn) rpn = RpnStack.restore(levels, entry, lift, keys)
    }

    fun reuse(entry: HistoryEntry) {
        status = ""
        if (isRpn) apply(rpn.reuse(entry.result)) else builder.insertResult(entry.result)
    }
    fun clearHistory() { commit(state.copy(history = emptyList())) }
    fun updateSettings(settings: Settings) {
        require(settings.decimalPlaces == null || settings.decimalPlaces in 0..6)
        require(settings.maxHistoryEntries == null || settings.maxHistoryEntries in 1..10000)
        require(settings.theme in setOf("dark", "light"))
        require(settings.inputMode in setOf("algebraic", "rpn"))
        val modeChanged = settings.inputMode != state.settings.inputMode
        commit(state.copy(settings = settings, history = trimHistory(state.history, settings.maxHistoryEntries)))
        // Unfinished input belongs to the mode it was typed in; history is kept.
        if (modeChanged) { builder.clear(); rpn = RpnStack(); status = "" }
    }
    private fun commit(updated: StoredState) { save(updated); state = updated }
}
