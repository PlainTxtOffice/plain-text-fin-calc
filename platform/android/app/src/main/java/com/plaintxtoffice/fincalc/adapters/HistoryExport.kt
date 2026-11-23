package com.plaintxtoffice.fincalc.adapters

import com.plaintxtoffice.fincalc.domains.calc.HistoryEntry
import java.io.Writer

/**
 * Write full precision CSV. The last column, rpn_input, holds the keys of a calculation made in
 * RPN mode and is empty for algebraic entries; ports without RPN mode write the first three columns.
 */
object HistoryExport {
    private fun cell(value: String): String = if (value.any { it in ",\"\n\r" })
        "\"${value.replace("\"", "\"\"")}\"" else value

    fun write(entries: List<HistoryEntry>, writer: Writer) {
        writer.write("timestamp,expression,result,rpn_input\n")
        entries.forEach {
            writer.write(listOf(it.timestamp.toString(), it.expression, it.result, it.rpnInput.orEmpty())
                .joinToString(",", transform = ::cell))
            writer.write("\n")
        }
    }
}
