package com.plaintxtoffice.fincalc.ui

import android.annotation.SuppressLint
import android.content.Context
import android.content.res.ColorStateList
import android.graphics.Canvas
import android.graphics.Paint
import android.graphics.drawable.RippleDrawable
import android.view.Gravity
import android.view.ViewGroup
import android.widget.LinearLayout
import android.widget.TextView
import androidx.core.graphics.drawable.toDrawable
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.plaintxtoffice.fincalc.R
import com.plaintxtoffice.fincalc.domains.calc.HistoryEntry
import com.plaintxtoffice.fincalc.domains.calc.formatResult

/** Recycle tape rows so large histories do not create thousands of views. */
// Constructed in Kotlin with required callbacks and theme colors; never inflated from XML.
@SuppressLint("ViewConstructor")
class TapeView(context: Context, private val colors: ThemeColors, private val reuse: (HistoryEntry) -> Unit) : RecyclerView(context) {
    private var entries: List<HistoryEntry> = emptyList()
    private var places: Int? = null
    private val rows = Rows()
    init {
        layoutManager = LinearLayoutManager(context).apply { stackFromEnd = true }
        adapter = rows
        addItemDecoration(Dividers(withAlpha(colors.muted, 0x30), context.dp(1)))
        contentDescription = context.getString(R.string.history_description)
    }

    fun showHistory(history: List<HistoryEntry>, decimalPlaces: Int?) {
        if (history == entries && decimalPlaces == places) return
        val historyChanged = history != entries
        val updates = historyDiff(entries, history, decimalPlaces != places)
        entries = history
        places = decimalPlaces
        updates.dispatchUpdatesTo(rows)
        if (historyChanged && entries.isNotEmpty()) scrollToPosition(entries.lastIndex)
    }

    /** Lines between rows only; a line under the newest row would sit against the panel edge. */
    private class Dividers(color: Int, private val height: Int) : ItemDecoration() {
        private val paint = Paint().apply { this.color = color }
        override fun onDraw(canvas: Canvas, parent: RecyclerView, state: State) {
            for (i in 0 until parent.childCount) {
                val child = parent.getChildAt(i)
                if (parent.getChildAdapterPosition(child) == state.itemCount - 1) continue
                val bottom = child.bottom + child.translationY
                canvas.drawRect(0f, bottom, parent.width.toFloat(), bottom + height, paint)
            }
        }
    }

    /** Right-aligned like an adding-machine tape, so digits of results line up down the column. */
    private class Row(val view: LinearLayout, val expression: TextView, val result: TextView) : ViewHolder(view)
    private inner class Rows : Adapter<Row>() {
        override fun getItemCount(): Int = entries.size
        override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): Row {
            val expression = TextView(context).apply {
                textSize = 14f; setTextColor(colors.muted); gravity = Gravity.END
                fontFeatureSettings = "tnum"
            }
            val result = TextView(context).apply {
                textSize = 20f; setTextColor(colors.text); gravity = Gravity.END
                fontFeatureSettings = "tnum"
            }
            val view = LinearLayout(context).apply {
                orientation = LinearLayout.VERTICAL
                layoutParams = LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.WRAP_CONTENT)
                minimumHeight = context.dp(56)
                gravity = Gravity.CENTER_VERTICAL
                setPadding(context.dp(16), context.dp(8), context.dp(16), context.dp(8))
                background = RippleDrawable(ColorStateList.valueOf(withAlpha(colors.text, 0x30)), null,
                    colors.text.toDrawable())
                addView(expression); addView(result)
            }
            return Row(view, expression, result)
        }
        override fun onBindViewHolder(holder: Row, position: Int) {
            val entry = entries[position]
            val expression = KeyLabels.format(entry.expression)
            val result = KeyLabels.format(formatResult(entry.result, places))
            holder.expression.text = expression
            holder.result.text = context.getString(R.string.history_result, result)
            holder.view.contentDescription = context.getString(R.string.history_entry_description, expression, result)
            holder.view.setOnClickListener { reuse(entry) }
        }
    }
}
