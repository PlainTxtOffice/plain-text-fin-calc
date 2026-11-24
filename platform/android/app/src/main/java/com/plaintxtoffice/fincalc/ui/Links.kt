package com.plaintxtoffice.fincalc.ui

import android.app.AlertDialog
import android.content.ActivityNotFoundException
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import androidx.core.net.toUri

const val PRIVACY_POLICY_URL = "https://plaintxtoffice.com/privacy-policy/"
const val CONTACT_URL = "https://plaintxtoffice.com/contact/"
/** Bug reports and feature requests; the same support address as the Play listing. */
const val FEEDBACK_EMAIL = "feedback@plaintxtoffice.com"
/** Same subject format as the other PlainTxtOffice apps; the version goes in the body instead. */
const val FEEDBACK_SUBJECT = "Plain Text Fin Calc feedback (Android)"

/** Opens [uri] in a browser, or shows the address when no browser is installed. */
fun Context.openLink(uri: Uri, title: String) {
    try { startActivity(Intent(Intent.ACTION_VIEW, uri)) }
    catch (_: ActivityNotFoundException) {
        AlertDialog.Builder(this).setTitle(title).setMessage("No browser is available.\n$uri")
            .setPositiveButton("OK", null).show()
    }
}

/** Lines under the writer's message that tell support which app, Android version, and device a report is about. */
fun feedbackDetails(version: String, androidRelease: String, apiLevel: Int, manufacturer: String, model: String): String =
    "\n\n---\nPlain Text Fin Calc $version\nAndroid $androidRelease (API $apiLevel)\n$manufacturer $model"

/** Asks how to send a bug report or feature request: an email draft or the website's contact form. */
fun Context.sendFeedback(version: String) {
    AlertDialog.Builder(this).setTitle("Send Feedback")
        .setMessage("Send a bug report or feature request by email or with the contact form on our website.")
        .setPositiveButton("Email") { _, _ -> emailFeedback(version) }
        .setNeutralButton("Contact form") { _, _ -> openLink(CONTACT_URL.toUri(), "Send Feedback") }
        .setNegativeButton("Cancel", null).show()
}

/**
 * Drafts a feedback email naming the app version, Android version, and device, which the sender can
 * see and delete. Shows the address when no mail app is installed.
 */
private fun Context.emailFeedback(version: String) {
    val draft = Intent(Intent.ACTION_SENDTO, "mailto:".toUri())
        .putExtra(Intent.EXTRA_EMAIL, arrayOf(FEEDBACK_EMAIL))
        .putExtra(Intent.EXTRA_SUBJECT, FEEDBACK_SUBJECT)
        .putExtra(Intent.EXTRA_TEXT, feedbackDetails(version, Build.VERSION.RELEASE, Build.VERSION.SDK_INT,
            Build.MANUFACTURER, Build.MODEL))
    try { startActivity(draft) }
    catch (_: ActivityNotFoundException) {
        AlertDialog.Builder(this).setTitle("Send Feedback")
            .setMessage("No email app is available. Send bug reports and feature requests to\n$FEEDBACK_EMAIL")
            .setPositiveButton("OK", null).show()
    }
}
