package com.plaintxtoffice.fincalc.domains.calc

/** One tape line produced by an RPN calculation, with the keys that led to it. */
data class RpnRecord(val expression: String, val result: String, val rpnInput: String)

/** The stack after an accepted key, and the tape line that key produced, if any. */
data class RpnStep(val stack: RpnStack, val record: RpnRecord? = null)

/**
 * Four-level reverse Polish stack (X, Y, Z, T) with stack lift. Levels can be empty, so
 * operands the user never entered cannot reach the tape. Every key returns a new value or
 * throws [EvaluationError] and leaves this value as it was. All arithmetic goes through
 * [Evaluator], so results equal the algebraic result of the same expression.
 *
 * [levels] lists X first. [entry] is the number being typed, shown as X while present.
 * [lift] is false only directly after ENTER, when the next number overwrites X.
 * [keys] logs the accepted keys since the last tape line.
 */
data class RpnStack(
    val levels: List<String> = emptyList(),
    val entry: String? = null,
    val lift: Boolean = true,
    val keys: List<String> = emptyList(),
) {
    /** The value on the Y line: the top of the stack while typing, else the second level. */
    val visibleY: String? get() = levels.getOrNull(if (entry != null) 0 else 1)

    fun press(key: String): RpnStep = when (key) {
        in DIGITS -> RpnStep(digit(key))
        "." -> RpnStep(point())
        "backspace" -> RpnStep(backspace())
        "sign" -> RpnStep(sign())
        "enter" -> RpnStep(enter())
        "swap" -> RpnStep(swap())
        "drop" -> RpnStep(drop())
        // Clear the typed number first; with none, clear the whole stack.
        "C" -> RpnStep(if (entry != null) copy(entry = null) else RpnStack())
        "log" -> log()
        in OPERATORS -> binary(key)
        else -> throw EvaluationError("Invalid input: $key")
    }

    /** Put a saved tape result in X: replaces a typed number or an ENTER duplicate, else lifts. */
    fun reuse(value: String): RpnStep {
        val number = canon(value)
        val updated = if (lift) pushed(levels, number) else listOf(number) + levels.drop(1)
        return RpnStep(RpnStack(updated, null, true, logged(keys, number)))
    }

    private fun startEntry(text: String) = copy(levels = if (lift) levels else levels.drop(1), entry = text, lift = true)

    private fun digit(key: String): RpnStack = when {
        entry == null -> startEntry(key)
        entry.count { it in '0'..'9' } < MAX_ENTRY_DIGITS -> copy(entry = entry + key)
        else -> throw EvaluationError("Invalid input: $key")
    }

    private fun point(): RpnStack = when {
        entry == null -> startEntry("0.")
        '.' !in entry -> copy(entry = "$entry.")
        else -> throw EvaluationError("Invalid input: .")
    }

    private fun backspace(): RpnStack {
        val rest = (entry ?: return this).dropLast(1)
        return copy(entry = rest.takeIf { text -> text.any { it in '0'..'9' } })
    }

    private fun sign(): RpnStack = when {
        entry != null -> copy(entry = if (entry.startsWith("-")) entry.drop(1) else "-$entry")
        levels.isEmpty() -> this
        else -> {
            val x = levels[0]
            // Zero is handled as text so that no negative zero can arise.
            val negated = if (x == "0") x else resultString(listOf("-", x)).let { if (isZeroText(it)) "0" else it }
            copy(levels = listOf(negated) + levels.drop(1), lift = true, keys = logged(keys, "CHS"))
        }
    }

    /** Push the typed number, if any, so every stack key sees it as X. */
    private fun terminated(): RpnStack {
        val number = canon(entry ?: return this)
        return copy(levels = pushed(levels, number), entry = null, keys = logged(keys, number))
    }

    private fun needing(count: Int): RpnStack = terminated().also {
        if (it.levels.size < count) throw EvaluationError("Too few operands")
    }

    private fun enter(): RpnStack = needing(1).run {
        copy(levels = pushed(levels, levels[0]), lift = false, keys = logged(keys, "ENTER"))
    }

    private fun swap(): RpnStack = needing(2).run {
        copy(levels = listOf(levels[1], levels[0]) + levels.drop(2), lift = true, keys = logged(keys, "SWAP"))
    }

    private fun drop(): RpnStack = needing(1).run {
        // A full stack repeats T as it drops.
        val rest = if (levels.size == MAX_LEVELS) levels.drop(1) + levels.last() else levels.drop(1)
        copy(levels = rest, lift = true, keys = logged(keys, "DROP"))
    }

    private fun binary(operator: String): RpnStep = needing(2).run {
        val y = levels[1]
        val x = levels[0]
        val result = resultString(listOf(y, operator, x))
        val rest = levels.drop(2) + if (levels.size == MAX_LEVELS) listOf(levels.last()) else emptyList()
        calculated(listOf(result) + rest, "$y $operator $x", result, operator)
    }

    private fun log(): RpnStep = needing(1).run {
        val x = levels[0]
        val result = resultString(listOf("log", "(", x, ")"))
        calculated(listOf(result) + levels.drop(1), "log ( $x )", result, "LOG")
    }

    private fun calculated(updated: List<String>, expression: String, result: String, key: String) =
        RpnStep(RpnStack(updated), RpnRecord(expression, result, logged(keys, key).joinToString(" ")))

    companion object {
        const val MAX_LEVELS = 4
        const val MAX_ENTRY_DIGITS = 28
        const val MAX_KEYS = 64
        private const val TRUNCATED = "..."
        private val DIGITS = ('0'..'9').map { it.toString() }.toSet()
        private val OPERATORS = setOf("+", "-", "*", "/", "^")
        private val LOG_WORDS = setOf("ENTER", "SWAP", "DROP", "CHS", "LOG", TRUNCATED) + OPERATORS
        private val ZERO_TEXT = Regex("-?(0+\\.?0*|\\.0+)")
        private val ENTRY_TEXT = Regex("-?[0-9]*\\.?[0-9]*")

        /** The string algebraic mode stores for the same tokens. */
        fun resultString(tokens: List<String>): String = plainResult(Evaluator.evaluate(tokens))

        /** True for any spelling of zero, such as 0, -0, 0. and -0.00. */
        fun isZeroText(text: String): Boolean = ZERO_TEXT.matches(text)

        /** The stored form of a typed or reused number; zero is decided by its text. */
        fun canon(text: String): String = if (isZeroText(text)) "0" else resultString(listOf(text))

        private fun pushed(levels: List<String>, value: String) = (listOf(value) + levels).take(MAX_LEVELS)

        /** Keep the newest keys; "..." in first place marks a shortened log. */
        private fun logged(keys: List<String>, token: String): List<String> {
            val all = keys + token
            return if (all.size <= MAX_KEYS) all else listOf(TRUNCATED) + all.drop(2)
        }

        /** Rebuild a stack from saved UI state; anything invalid gives the empty stack. */
        fun restore(levels: List<String>, entry: String?, lift: Boolean, keys: List<String>): RpnStack {
            if (levels.size > MAX_LEVELS || keys.size > MAX_KEYS) return RpnStack()
            val typed = entry?.takeIf { it.isNotEmpty() }
            if (typed != null) {
                val digits = typed.count { it in '0'..'9' }
                if (!lift || !ENTRY_TEXT.matches(typed) || digits !in 1..MAX_ENTRY_DIGITS) return RpnStack()
            }
            return try {
                val numbers = levels.map(::canon)
                keys.forEach { if (it !in LOG_WORDS) canon(it) }
                if (!lift && (numbers.size < 2 || numbers[0] != numbers[1])) RpnStack()
                else RpnStack(numbers, typed, lift, keys.toList())
            } catch (error: EvaluationError) { RpnStack() }
        }
    }
}
