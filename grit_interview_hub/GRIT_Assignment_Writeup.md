# GRIT Interview Scheduling — Product Write-up

## 1. Student interview states

| State | Entry condition / transition |
|---|---|
| Not eligible | Required skills, attendance, registration or conduct checks are incomplete. Moves to Eligible when every rule passes. |
| Eligible | All required skill levels for the selected track/badge are cleared and programme eligibility checks pass. Student can view open slots. |
| Scheduled | Student confirms an open slot. Slot is atomically marked booked and assigned to one interviewer. |
| Completed — Pass | Interviewer records Pass and feedback. Moves to Badge awarded only after final eligibility validation. |
| Completed — Fail | Interviewer records Fail and feedback. Student sees the result and next-step guidance; reattempt policy is controlled by the team. |
| Retake required | Interviewer requests another attempt later. The student can book a new slot; the old interview remains in history. |
| No-show | Interviewer marks the student absent. Team reviews and decides whether rebooking is allowed. |
| Cancelled / Rescheduled | Authorised team action or approved student cancellation. The old slot is released only when cancellation is confirmed; rescheduling creates a new booking record or linked booking event. |
| Badge awarded | Interview passed and all badge prerequisites revalidated. |
| Badge nullified | A verified later malpractice finding revokes badge validity. Original interview and award records remain for audit. |

**Key modelling choice:** interview outcome and badge validity are separate. A later malpractice flag must not rewrite a historical Pass into Fail. It changes the badge to Nullified and records who acted, when, and why.

## 2. Edge cases and assumptions

- **Double booking:** use an atomic conditional slot update inside a database transaction; only one booking can claim an OPEN slot.
- **Duplicate active booking:** allow at most one active interview per student + track + badge. Enforce in the service layer and, in production, with a partial unique database index.
- **Interviewer overlap:** reject overlapping availability windows for the same interviewer.
- **Past slots:** reject booking and publishing availability in the past.
- **Student no-show:** interviewer marks No-show; operations team decides whether a penalty or rebooking applies.
- **Interviewer absence:** operations team reassigns the interview or offers a replacement slot; notify the student.
- **Retake:** preserve the previous attempt and feedback; create a new booking for the next attempt.
- **Malpractice discovered after pass:** nullify the badge, retain interview history, record case reference and actor, and notify the student.
- **Eligibility changes after booking:** freeze eligibility snapshot at booking; if a material policy issue appears, operations can put the booking on hold and review it.
- **No slots:** show a clear empty state and allow the student to revisit; operations sees eligible-but-unbooked students.
- **Incorrect outcome:** allow only authorised correction with old value, new value, reason and actor in audit log.
- **Timezone / daylight saving:** store timestamps in UTC in production and render in the student's/interviewer's configured timezone.
- **Privacy:** students see only their own records; interviewers see assigned interviews; operations sees programme-wide records.
- **Assumptions:** one active booking per student per badge; interviewers own their availability; Pass is necessary but not sufficient for badge award; Retake requires a fresh slot; only authorised operations staff can nullify badges.

## 3. Data model

- **students**(`student_id` PK, name, email, attendance, registration_status, conduct_status, track, badge_level, skills_completed, required_skills)
- **interviewers**(`interviewer_id` PK, name, email, active)
- **availability_slots**(`slot_id` PK, `interviewer_id` FK, start_time, end_time, status: OPEN/BOOKED/BLOCKED)
- **interviews**(`interview_id` PK, `student_id` FK, `interviewer_id` FK, `slot_id` FK, track, badge_level, status, outcome, feedback, booked_at, completed_at)
- **badges**(`badge_id` PK, `student_id` FK, track, badge_level, status: PENDING/AWARDED/NULLIFIED, awarded_at, nullified_at, nullification_reason)
- **audit_logs**(`log_id` PK, actor, entity_type, entity_id, action, old_value, new_value, created_at)
- Production additions: `users/roles`, `notifications`, `booking_events`, `malpractice_cases`, `eligibility_snapshots`, and `tracks/badge_requirements`.

## 4. Three student-facing messages

1. **Booking confirmation:** “Your GRIT interview is confirmed for [date] at [time] with [interviewer]. Please join on time and keep your project work ready. You can view the details in your dashboard.”
2. **Pass:** “Congratulations! You have cleared your [badge level] interview for [track]. Your badge is now awarded and will be visible on your GRIT dashboard.”
3. **Retake:** “Your interview team has requested a retake. Please review the feedback below, prepare the suggested areas, and book a new available slot from your dashboard.”

## 5. Before / after screens

- **Before interview:** student home shows skills progress, eligibility checklist, “Book interview” CTA, and “Not booked” status.
- **After booking:** replace CTA with confirmed date, time, interviewer and preparation instructions.
- **After Pass:** show awarded badge, interview result and next badge progression (if unlocked).
- **After Fail / Retake:** show result, interviewer feedback and next action; do not show an awarded badge.
- **After malpractice:** show “Badge nullified — contact the GRIT team”; retain the historical interview result internally and in the student's history where policy permits.

## Product metrics
Track eligible-to-book conversion, median time from eligibility to booking, slot utilisation, no-show rate, interviewer utilisation, outcome distribution, retake rate, and time from Pass to badge award.
