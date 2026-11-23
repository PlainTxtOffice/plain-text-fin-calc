package com.plaintxtoffice.fincalc

import android.app.AlertDialog
import androidx.core.net.toUri
import android.os.Bundle
import android.view.ContextThemeWrapper
import android.view.Gravity
import android.widget.*
import androidx.activity.ComponentActivity
import androidx.activity.result.contract.ActivityResultContracts
import androidx.core.view.ViewCompat
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import androidx.lifecycle.ViewModelProvider
import com.plaintxtoffice.fincalc.application.CalculatorModel
import com.plaintxtoffice.fincalc.application.ScreenState
import com.plaintxtoffice.fincalc.ui.*

/** Android lifecycle and document-picker boundary; calculations live in the domain. */
class MainActivity : ComponentActivity() {
    private lateinit var model: CalculatorModel
    private lateinit var calculator: CalculatorView
    private var shownTheme: String? = null
    private val export = registerForActivityResult(ActivityResultContracts.CreateDocument("text/csv")) { uri ->
        if (uri != null) model.export(uri)
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        WindowCompat.setDecorFitsSystemWindows(window, false)
        model = ViewModelProvider(this)[CalculatorModel::class.java]
        if (savedInstanceState != null && !model.current.ready) {
            model.restore(savedInstanceState.getStringArrayList("tokens") ?: emptyList(),
                savedInstanceState.getBoolean("pending"))
        }
        render(model.current)
    }

    override fun onStart() {
        super.onStart()
        model.onChange = ::render
        render(model.current)
    }
    override fun onStop() { model.onChange = null; super.onStop() }
    override fun onSaveInstanceState(outState: Bundle) {
        outState.putStringArrayList("tokens", ArrayList(model.current.tokens))
        outState.putBoolean("pending", model.current.pending)
        super.onSaveInstanceState(outState)
    }

    private fun render(state: ScreenState) {
        if (shownTheme != state.stored.settings.theme) buildViews(state.stored.settings.theme)
        calculator.render(state)
    }

    private fun buildViews(theme: String) {
        shownTheme = theme
        val colors = ThemeColors.forName(this, theme)
        val root = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL; setBackgroundColor(colors.background) }
        val bar = LinearLayout(this).apply { gravity = Gravity.CENTER_VERTICAL }
        bar.addView(TextView(this).apply { setText(R.string.app_name); textSize = 22f; setTextColor(colors.text) },
            LinearLayout.LayoutParams(0, dp(48), 1f))
        bar.addView(Button(this).apply {
            text = "⋮"; textSize = 24f; contentDescription = "More options"
            setTextColor(colors.text); background = pressable(colors.surface, colors.text)
            setOnClickListener { showMenu(this) }
        }, LinearLayout.LayoutParams(dp(48), dp(48)))
        root.addView(bar)
        calculator = CalculatorView(this, colors, model::press, model::reuse)
        root.addView(calculator, LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, 0, 1f))
        ViewCompat.setOnApplyWindowInsetsListener(root) { view, insets ->
            val bars = insets.getInsets(WindowInsetsCompat.Type.systemBars() or WindowInsetsCompat.Type.displayCutout())
            view.setPadding(bars.left + dp(12), bars.top + dp(8), bars.right + dp(12), bars.bottom + dp(8))
            insets
        }
        setContentView(root)
        WindowCompat.getInsetsController(window, root).apply {
            isAppearanceLightStatusBars = theme == "light"
            isAppearanceLightNavigationBars = theme == "light"
        }
    }

    private fun showMenu(anchor: Button) {
        if (!model.current.ready) return
        val context = ContextThemeWrapper(this, dialogTheme(shownTheme))
        PopupMenu(context, anchor).apply {
            listOf("Settings", "Export History", "Clear History", "Send Feedback", "Privacy Policy", "About").forEach { menu.add(it) }
            setOnMenuItemClickListener { item ->
                when (item.title) {
                    "Settings" -> showSettings(context, model.current.stored.settings, model::updateSettings)
                    "Export History" -> export.launch("plain-text-fin-calc-history.csv")
                    "Send Feedback" -> context.sendFeedback(BuildConfig.VERSION_NAME)
                    "Privacy Policy" -> context.openLink(PRIVACY_POLICY_URL.toUri(), "Privacy Policy")
                    "Clear History" -> AlertDialog.Builder(context).setTitle("Clear History?")
                        .setMessage("Remove all saved calculations from this device?")
                        .setNegativeButton("Cancel", null)
                        .setPositiveButton("Clear") { _, _ -> model.clearHistory() }.show()
                    "About" -> AlertDialog.Builder(context).setTitle("Plain Text Fin Calc ${BuildConfig.VERSION_NAME}")
                        .setMessage("Decimal calculator by Plain Text Office.\n\nTap a tape result to reuse its full precision. Use log ( … ) for base-10 logarithms.\n\nOpen source under the MIT License · Copyright 2026 Plain Text Office LLC")
                        .setPositiveButton("OK", null).show()
                }
                true
            }
            show()
        }
    }
}
