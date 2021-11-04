# ElapseAnalyzer
Simple WCL Analyzer for fight report

### Scenario 1
Calculate parse% + bracket% Per DPS Character Per Encounter

### [TODO]Scenario 2

Calculate DPS Character Fight Potion

### [TODO]Scenario 3 

Get Healer Casts durning Entire Raid

### [TODO]Scenario 4 

Get Healer Overhealed Volume % during Entire Raid

### [TODO]Scenario 5 

Get Healer Potion during Entire Raid

### Usage 1:
```sh
# invoke py directly with -l and your wcl fight report link
python elapse_wcl_analyzer.py -l https://cn.classic.warcraftlogs.com/reports/rwG81bzxZvg3mDN9
```

Output:
`elapse_score.csv`


### [TODO]Usage 2:
```sh
# invoke py directly with -l and your wcl fight report link
python elapse_wcl_analyzer.py -o html -l https://cn.classic.warcraftlogs.com/reports/rwG81bzxZvg3mDN9
```

Output:
html web content

