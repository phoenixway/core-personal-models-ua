---
up:
  - "[[01-life-management-model]]"
---
app/src/main/java/com/romankozak/forwardappmobile/data/dao/ActivityRecordDao.kt
app/src/main/java/com/romankozak/forwardappmobile/data/repository/ActivityRecordRepository.kt
app/src/main/java/com/romankozak/forwardappmobile/data/repository/ActivityRepository.kt
app/src/main/java/com/romankozak/forwardappmobile/features/activitytracker/ActivityTrackerScreen.kt
app/src/main/java/com/romankozak/forwardappmobile/features/activitytracker/ActivityTrackerViewModel.kt

маю фічу трекера активності. в ui вона називається "Журналом Життя". теп по картці запису активності викликає діалог редагування. в якому файлі він реалізований?

 ▎   cat > activity_tracker_edit_dialog_summary.txt << 'EOF'
 ▎   The edit dialog for activity record cards is implemented as a private
 ▎   composable function `EditRecordDialog` within `ActivityTrackerScreen.kt`
 ▎   (lines 1304–1440). This dialog provides:
 ▎
 ▎   - **Record type selection** (comment, instant event, timed activity) via
 ▎   filter chips
 ▎   - **Text field** for editing the activity description
 ▎   - **Time pickers** for start/end times (with validation)
 ▎   - **XP fields** for gained/lost experience points
 ▎   - **Integration** with the view model's `onRecordUpdated` method
 ▎
 ▎   The dialog is triggered when `editingRecord` is non‑null in the view
 ▎   model, and it handles both timeless comments and timed activities.
 ▎   Additionally, the `dialogs/` subdirectory contains a `TimePickerDialog.kt`
 ▎   used for picking individual time values within the edit flow.
 ▎
 ▎   If you need to examine the exact implementation, the full
 ▎   `EditRecordDialog` function is already present in the provided
 ▎   `ActivityTrackerScreen.kt` content.
 ▎   EOF
 ▎
