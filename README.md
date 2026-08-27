# Tata Power EZ Charge — EV Charging Network Analytics

An end-to-end business analytics project inspired by Tata Power EZ Charge, focused on understanding EV charging demand, customer behaviour, network utilization, and the potential to shift flexible charging demand away from peak periods.

The project combines **network analytics, customer segmentation, behavioural scoring, experimentation, statistical inference, unit economics, and strategic recommendations** into a single decision-making framework.

> **Note:** This is an independent portfolio project using synthetically generated data. It is not affiliated with or endorsed by Tata Power and does not use Tata Power proprietary data.


## Business Problem

EV charging demand is not evenly distributed across time and locations. High-demand periods can create utilization pressure at specific stations, while charging capacity may remain underutilized during other periods.

Rather than relying only on infrastructure expansion, the project investigates whether some flexible charging demand can be shifted from peak to off-peak periods through targeted customer interventions.

## Core Business Question

> **Can Tata Power improve charging-network utilization and economics by identifying flexible customers and incentivizing them to charge during lower-demand periods?**

The analysis therefore answers five practical questions:

- **Who** should be targeted?
- **When** should charging be shifted?
- **Where** should interventions be prioritized?
- **How much** incentive makes economic sense?
- **Should** the intervention be scaled?


## Project Approach

The project follows an end-to-end analytics pipeline:

**Network & Market Analytics**  
↓  
**Customer Behaviour**  
↓  
**Customer Segmentation**  
↓  
**Charging Flexibility Scoring**  
↓  
**Intervention Strategy**  
↓  
**A/B Experiment Design**  
↓  
**Statistical Analysis**  
↓  
**Unit Economics**  
↓  
**Business Recommendation**

This moves beyond descriptive dashboards to evaluate whether an identified opportunity can actually translate into measurable and economically viable business impact.



## Dataset

A synthetic EV charging ecosystem was programmatically generated to represent the structure and behavioural characteristics of a large charging network.

| Entity | Volume |
|---|---:|
| Customers | 8,000 |
| Stations | 150 |
| Chargers | 1,351 |
| Charging sessions | 1,087,262 |
| Simulation period | Jan–Dec 2026 |

The generated data includes customer attributes, charging behaviour, stations, chargers, session timing, energy consumption, charging outcomes, and network relationships.

The data-generation pipeline is reproducible through Python scripts in `src/`.



### 1. Network & Market Analytics

The first stage establishes the baseline state of the charging network.

Analysis includes:

- Hourly and monthly charging demand
- Peak vs. off-peak utilization
- City-level demand
- Station performance
- Charger-type performance
- Session and energy patterns
- Network concentration
- Peak-demand pressure

The objective is to identify where demand pressure exists and distinguish between genuine capacity constraints and demand that may be manageable through behavioural interventions.



### 2. Customer Behaviour & Segmentation

Customer-level behaviour is analysed across dimensions such as:

- Charging frequency
- Energy consumption
- Charging timing
- Peak dependence
- Charging regularity
- Station usage
- Network engagement

Customers are then segmented based on behavioural characteristics to identify groups with meaningfully different charging patterns.

The segmentation is designed to support **business targeting**, rather than simply creating statistical clusters.



### 3. Charging Flexibility & Intervention Targeting

A charging flexibility framework is used to identify customers who are more likely to change when they charge.

The analysis considers behavioural signals such as:

- Historical charging-time variation
- Peak-period dependence
- Charging regularity
- Usage frequency
- Behavioural flexibility

This creates a targeted intervention population instead of applying incentives across the entire customer base.

Customer and segment opportunity scores are then combined with city-level network conditions to identify priority intervention opportunities.



### 4. A/B Experiment

The intervention is evaluated through a controlled experiment.

### Control

Customers continue under the existing charging conditions.

### Treatment

Eligible customers receive a targeted time-based incentive intended to encourage charging during lower-demand periods.

The experiment measures whether treatment customers demonstrate a greater shift in charging behaviour than the control group.

The analysis includes:

- Treatment/control comparison
- Response rates
- Peak-session shift rates
- Absolute treatment effect
- Relative treatment effect
- Statistical significance
- 95% confidence intervals
- Segment-level treatment effects



### 5. Unit Economics

A statistically significant intervention is not automatically a good business decision.

The project therefore evaluates the economics of the observed treatment effect through:

- Incremental shifted sessions
- Intervention cost
- Incremental value
- Net incremental value
- ROI
- Cost per incremental shifted session
- Break-even analysis
- Scale-up economics
- Sensitivity analysis

The economic assumptions are explicitly modelled and tested rather than presented as Tata Power's actual commercial pricing or margins.



## Key Experimental & Economic Results

The experiment produced the following illustrative results:

| Metric | Result |
|---|---:|
| Treatment customers | 2,357 |
| Control shift rate | 11.52% |
| Treatment shift rate | 16.19% |
| Incremental shift rate | **+4.67 pp** |
| Incremental shifted sessions | **5,235** |
| Incremental value | **₹104,700** |
| Intervention cost | **₹11,785** |
| Net incremental value | **₹92,915** |
| ROI | **788.42%** |

The intervention therefore shows a positive economic outcome under the project's base-case assumptions.

The project also evaluates how the economics change when intervention cost and value per shifted session vary, providing a sensitivity-based view of the scale-up decision.



## Final Recommendation

The analysis identifies:

### Priority Customer Segment
**High_Mileage**

Customers in this segment show the strongest observed response and represent the most attractive initial target for demand-shifting interventions.

### Priority City
**Delhi NCR**

Delhi NCR emerges as the highest-priority city based on the intervention opportunity analysis.

### Recommended Strategy

Rather than offering a broad discount to the entire customer base:

1. Identify customers with high charging flexibility.
2. Prioritize high-response customer segments.
3. Focus interventions on peak periods with meaningful network pressure.
4. Prioritize cities/stations where demand shifting can relieve utilization pressure.
5. Use controlled experimentation to continuously measure behavioural response.
6. Scale only where incremental value exceeds intervention cost.

### Decision

**SCALE the targeted intervention**, subject to validation of the underlying commercial assumptions and real-world pilot results.

The broader strategic takeaway is:

> **Demand shifting can complement infrastructure expansion by using customer behaviour to better balance existing charging capacity.**



## Project Structure

```text
tata-power-ev-charging-analytics/
│
├── data/
│   └── raw/
│
├── notebooks/
│   ├── 02_market_analytics.ipynb
│   ├── 03_customer_behaviour.ipynb
│   ├── 04_intervention_strategy.ipynb
│   ├── 05_experiment_design.ipynb
│   ├── 06_experiment_analysis.ipynb
│   ├── 07_unit_economics.ipynb
│   ├── 08_recommendation.ipynb
│   └── 09_project_qa.ipynb
│
├── outputs/
│   ├── figures/
│   └── tables/
│
├── src/
│   ├── generate_chargers.py
│   ├── generate_customers.py
│   ├── generate_network.py
│   └── generate_sessions.py
│
└── .gitignore
````



## Tools & Technologies

**Python · Pandas · NumPy · SciPy · SQL · Jupyter Notebook · Matplotlib · Git · GitHub**

## Analytical Methods

* Exploratory Data Analysis
* Feature Engineering
* Customer Segmentation
* Behavioural Scoring
* Network & Utilization Analysis
* A/B Testing
* Statistical Inference
* Treatment Effect Analysis
* Unit Economics
* Break-Even Analysis
* Sensitivity Analysis



## Data & Disclaimer

The project uses **synthetically generated data** created specifically for this portfolio analysis.

The large session-level dataset is excluded from GitHub because it exceeds GitHub's individual file-size limit; the data-generation scripts and analytical outputs remain available in the repository.

The business context is inspired by publicly discussed EV charging-network dynamics. All customer data, charging sessions, experimental outcomes, economic assumptions, and recommendations in this project are illustrative.
