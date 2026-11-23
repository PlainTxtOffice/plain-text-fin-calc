package com.plaintxtoffice.fincalc.ui

import android.app.AlertDialog
import android.content.Context
import android.text.InputType
import android.widget.*
import com.plaintxtoffice.fincalc.R
import com.plaintxtoffice.fincalc.config.Settings
import com.plaintxtoffice.fincalc.domains.calc.DecimalMath
import java.util.Locale

/** Edit presentation preferences, the input mode, and the history retention cap. */
fun showSettings(context: Context, settings: Settings, save: (Settings) -> Unit) {
    val form = LinearLayout(context).apply {
        orientation = LinearLayout.VERTICAL
        setPadding(context.dp(20), context.dp(8), context.dp(20), 0)
    }
    fun choices(label: String, options: List<String>, selection: Int): Spinner {
        form.addView(TextView(context).apply { text = label })
        return Spinner(context).apply {
            adapter = ArrayAdapter(context, android.R.layout.simple_spinner_dropdown_item, options)
            contentDescription = label
            setSelection(selection)
            form.addView(this)
        }
    }
    form.addView(TextView(context).apply {
        text = context.resources.getQuantityString(
            R.plurals.settings_precision,
            DecimalMath.context.precision, DecimalMath.context.precision,
        )
    })
    form.addView(TextView(context).apply {
        setText(R.string.settings_precision_explanation)
        setPadding(0, context.dp(4), 0, context.dp(16))
    })
    val places = choices(context.getString(R.string.settings_decimal_places),
        listOf(context.getString(R.string.settings_all_digits)) + (0..6).map { it.toString() },
        settings.decimalPlaces?.plus(1) ?: 0)
    form.addView(TextView(context).apply {
        setText(R.string.settings_rounding_explanation)
        setPadding(0, context.dp(4), 0, context.dp(16))
    })
    val mode = choices(context.getString(R.string.settings_input_mode),
        listOf(context.getString(R.string.settings_input_mode_algebraic), context.getString(R.string.settings_input_mode_rpn)),
        if (settings.inputMode == "rpn") 1 else 0)
    form.addView(TextView(context).apply {
        setText(R.string.settings_input_mode_explanation)
        setPadding(0, context.dp(4), 0, context.dp(16))
    })
    val theme = choices(context.getString(R.string.settings_theme),
        listOf(context.getString(R.string.settings_theme_dark), context.getString(R.string.settings_theme_light)),
        if (settings.theme == "light") 1 else 0)
    val unlimited = Switch(context).apply { setText(R.string.settings_unlimited_history); isChecked = settings.maxHistoryEntries == null }
    form.addView(unlimited)
    form.addView(TextView(context).apply { setText(R.string.settings_history_limit) })
    val cap = EditText(context).apply {
        inputType = InputType.TYPE_CLASS_NUMBER
        contentDescription = context.getString(R.string.settings_history_limit_description)
        // Match the integer parser with ungrouped digits in the editable field.
        setText(String.format(Locale.ROOT, "%d", settings.maxHistoryEntries ?: 1000))
        isEnabled = !unlimited.isChecked
    }
    form.addView(cap)
    unlimited.setOnCheckedChangeListener { _, checked -> cap.isEnabled = !checked }
    val scroll = ScrollView(context).apply { addView(form) }
    val dialog = AlertDialog.Builder(context).setTitle(R.string.settings_title).setView(scroll)
        .setNegativeButton(R.string.action_cancel, null).setPositiveButton(R.string.action_save, null).create()
    dialog.setOnShowListener {
        dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener {
            val limit = if (unlimited.isChecked) null else cap.text.toString().toIntOrNull()
            if (!unlimited.isChecked && (limit == null || limit !in 1..10000)) {
                cap.error = context.getString(R.string.settings_history_limit_error)
            } else {
                save(Settings(if (places.selectedItemPosition == 0) null else places.selectedItemPosition - 1,
                    if (theme.selectedItemPosition == 1) "light" else "dark", limit,
                    if (mode.selectedItemPosition == 1) "rpn" else "algebraic"))
                dialog.dismiss()
            }
        }
    }
    dialog.show()
}
