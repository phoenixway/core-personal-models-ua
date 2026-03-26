IF weekState == W0:
    PlanWeekFromStrategy()
    weekState = W1

IF weekState == W1:
    MonitorLeads()
    IF WeekEnded:
        weekState = W2

IF weekState == W2:
    WeeklyReview()
    weekState = W0