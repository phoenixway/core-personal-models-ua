IF strategyState == S0:
    WAIT until ReviewTrigger
    strategyState = S1

IF strategyState == S1:
    AnalyzeLeadLag()
    IF values unclear:
        strategyState = S2
    ELSE:
        strategyState = S3

IF strategyState == S2:
    ClarifyMainBeacons()
    IF beacons clear:
        strategyState = S3

IF strategyState == S3:
    PrioritizeBeacons()
    IF priorities resolved:
        strategyState = S4
    ELSE:
        strategyState = S5

IF strategyState == S5:
    MaintainBaseline()
    WAIT until decision matures

IF strategyState == S4:
    DesignInitiativesAndSystems()
    strategyState = S0
