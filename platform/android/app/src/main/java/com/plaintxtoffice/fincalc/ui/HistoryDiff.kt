package com.plaintxtoffice.fincalc.ui

import androidx.recyclerview.widget.DiffUtil
import com.plaintxtoffice.fincalc.domains.calc.HistoryEntry

/** Preserve retained rows when history is appended, trimmed, or cleared; rebind when precision changes. */
internal fun historyDiff(
    previous: List<HistoryEntry>,
    next: List<HistoryEntry>,
    precisionChanged: Boolean,
): DiffUtil.DiffResult = DiffUtil.calculateDiff(object : DiffUtil.Callback() {
    override fun getOldListSize(): Int = previous.size
    override fun getNewListSize(): Int = next.size
    // Equal entries are interchangeable, including duplicate calculations with the same timestamp.
    override fun areItemsTheSame(oldItemPosition: Int, newItemPosition: Int): Boolean =
        previous[oldItemPosition] == next[newItemPosition]
    override fun areContentsTheSame(oldItemPosition: Int, newItemPosition: Int): Boolean =
        !precisionChanged && previous[oldItemPosition] == next[newItemPosition]
}, false)
