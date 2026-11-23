/// Unfinished input as kept in saved scene state between launches.
///
/// Lists are joined by one space. Only the values of the active input
/// mode are filled; the other mode's values are empty.
struct SavedInput: Equatable, Sendable {
    /// Tokens of the algebraic expression being entered.
    var tokens = ""
    /// True while the algebraic input ends in a reused result.
    var resultPending = false
    /// RPN stack values, X first.
    var rpnLevels = ""
    /// The number being typed in RPN mode; empty when there is none.
    var rpnEntry = ""
    /// False directly after ENTER.
    var rpnLiftEnabled = true
    /// RPN keystrokes accepted since the last tape entry.
    var rpnKeys = ""
}
