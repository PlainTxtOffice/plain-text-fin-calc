package com.plaintxtoffice.fincalc.ui

import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListUpdateCallback
import com.plaintxtoffice.fincalc.domains.calc.HistoryEntry
import org.junit.Assert.*
import org.junit.Test
import java.time.Instant

class HistoryDiffTest {
    private val first = HistoryEntry("1", "1", Instant.EPOCH)
    private val second = HistoryEntry("2", "2", Instant.EPOCH)
    private val third = HistoryEntry("3", "3", Instant.EPOCH)

    private class Updates : ListUpdateCallback {
        var inserted = 0
        var removed = 0
        var changed = 0
        var moved = 0
        override fun onInserted(position: Int, count: Int) { inserted += count }
        override fun onRemoved(position: Int, count: Int) { removed += count }
        override fun onChanged(position: Int, count: Int, payload: Any?) { changed += count }
        override fun onMoved(fromPosition: Int, toPosition: Int) { moved++ }
    }

    @Test fun appendKeepsExistingRows() {
        val result = historyDiff(listOf(first), listOf(first, second), precisionChanged = false)
        val updates = Updates().also(result::dispatchUpdatesTo)
        assertEquals(0, result.convertOldPositionToNew(0))
        assertEquals(1, updates.inserted)
        assertEquals(0, updates.removed + updates.changed + updates.moved)
    }

    @Test fun cappedAppendKeepsRetainedRows() {
        val result = historyDiff(listOf(first, second), listOf(second, third), precisionChanged = false)
        val updates = Updates().also(result::dispatchUpdatesTo)
        assertEquals(DiffUtil.DiffResult.NO_POSITION, result.convertOldPositionToNew(0))
        assertEquals(0, result.convertOldPositionToNew(1))
        assertEquals(1, updates.inserted)
        assertEquals(1, updates.removed)
        assertEquals(0, updates.changed + updates.moved)
    }

    @Test fun precisionChangeRebindsRetainedRows() {
        val entries = listOf(first, second)
        val result = historyDiff(entries, entries, precisionChanged = true)
        val updates = Updates().also(result::dispatchUpdatesTo)
        assertEquals(2, updates.changed)
        assertEquals(0, updates.inserted + updates.removed + updates.moved)
    }

    @Test fun clearRemovesAllRows() {
        val result = historyDiff(listOf(first, second), emptyList(), precisionChanged = false)
        val updates = Updates().also(result::dispatchUpdatesTo)
        assertEquals(2, updates.removed)
        assertEquals(0, updates.inserted + updates.changed + updates.moved)
    }

    @Test fun identicalEntriesRemainValidWhenTrimmed() {
        val result = historyDiff(listOf(first, first), listOf(first), precisionChanged = false)
        val updates = Updates().also(result::dispatchUpdatesTo)
        assertEquals(1, updates.removed)
        assertEquals(0, updates.inserted + updates.changed + updates.moved)
        assertTrue(result.convertNewPositionToOld(0) in 0..1)
    }

    @Test fun unchangedHistoryNeedsNoUpdates() {
        val entries = listOf(first, second)
        val result = historyDiff(entries, entries, precisionChanged = false)
        val updates = Updates().also(result::dispatchUpdatesTo)
        assertEquals(0, updates.inserted + updates.removed + updates.changed + updates.moved)
    }
}
