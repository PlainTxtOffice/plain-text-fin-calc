package com.plaintxtoffice.fincalc.ui

import android.content.Context
import android.content.res.ColorStateList
import android.graphics.Color
import android.graphics.drawable.GradientDrawable
import android.graphics.drawable.RippleDrawable
import com.plaintxtoffice.fincalc.R

/** Colors shared by calculator views; the preference belongs to the configuration model. */
data class ThemeColors(val background: Int, val surface: Int, val key: Int, val text: Int, val muted: Int, val accent: Int) {
    companion object {
        /** Reads the palette in colors.xml, which the app's styles share. */
        fun forName(context: Context, name: String): ThemeColors = if (name == "light") ThemeColors(
            context.getColor(R.color.light_background), context.getColor(R.color.light_surface),
            context.getColor(R.color.light_key), context.getColor(R.color.light_text),
            context.getColor(R.color.light_muted), context.getColor(R.color.light_accent),
        ) else ThemeColors(
            context.getColor(R.color.dark_background), context.getColor(R.color.dark_surface),
            context.getColor(R.color.dark_key), context.getColor(R.color.dark_text),
            context.getColor(R.color.dark_muted), context.getColor(R.color.dark_accent),
        )
    }
}

/** The activity theme for a saved theme name. */
fun appTheme(name: String?): Int = if (name == "light") R.style.AppTheme_Light else R.style.AppTheme
/** The menu and dialog theme for a saved theme name. */
fun dialogTheme(name: String?): Int = if (name == "light") R.style.AppDialog_Light else R.style.AppDialog

fun Context.dp(value: Int): Int = (value * resources.displayMetrics.density).toInt()
fun Context.rounded(color: Int, radiusDp: Int = 12): GradientDrawable = GradientDrawable().apply {
    setColor(color); cornerRadius = dp(radiusDp).toFloat()
}
/** A rounded fill that shows a ripple while pressed; the plain fill alone gives no touch feedback. */
fun Context.pressable(color: Int, ripple: Int, radiusDp: Int = 12): RippleDrawable =
    RippleDrawable(ColorStateList.valueOf(withAlpha(ripple, 0x40)), rounded(color, radiusDp), null)
fun withAlpha(color: Int, alpha: Int): Int = Color.argb(alpha, Color.red(color), Color.green(color), Color.blue(color))
