# bbrec_engine
# Summary
---
In this project, I created an ML algorithm that guesses the bug bounty price range for a given vulnerability. 

**Problem:** Currently, there is a big challenge in the field of Security Disclosure in determining how much a bug bounty should cost or how much a researcher should get paid for their responsible disclosure. 

Each company tends to select its own price ranges for bug bounties based on the multitude of factors, such as: 
 - how much they can afford to pay (this often boils down to company size, revenue, etc.)
 - location of the company (major tech cities tend to pay more)
 - the type of vulnerability and the affected scope
 - the severity of vulnerability
 - how much they believe a bug should be worth (highly subjective)
 - others

**Goal:** Our goal for this project is to capture some of these factors in the dataset and create an ML algorithm that is able to accurately discern the price range of a given vulnerability based on some of these factors.

At the very minimum, the user should be able to supply the **Type of Vulnerability, and its Severity**, and the ML engine would guess the price range of how much it's worth. 

**Usability:** I forsee this will be used by companies as a recommendation engine API to determine how much they should pay for bug bounties and existing vulnerabilities that have occurred. This could be offered as a free service at first to gather data and improve the ML engine. Once the accuracy is sufficient, it could become a paid service.

## Data Gathering
We want to gather existing data on paid vulnerabilities. Ideally, we want to gather as much information about the vulnerability as possible (this would comprise our training/test dataset) and an actual price that was paid (this would be our target label). 

This is a fairly difficult dataset to obtain, since the information is quite sensitive and unless both, the company and the dev agreed to disclose the bounty report, this information is typically unavailable.

**To my knowledge, there are no public datasets available that include bug bounty reports and their corresponding paid rewards.**

To collect this data, I decided to write a custom crawler for HackerOne that scouts the site for disclosed bug reports (only a fraction of them is mutually disclosed) and intelligently extracts specific fields of each report using jQuery. jQuery is handy for finding DOM elements and extracting data from them. I used Apify webscraper api and built my own crawler code on top of it that you can find [here](https://raw.githubusercontent.com/ekotysh/bbrec_engine/main/crawler/apify_code.js).


Using this technique, **I was able to obtain 2415 records** after 4 hours of runtime. 


## Data Preparation & Analysis
###  1. Removing critical missing data ###
The initial data I crawled contained a lot of missing information. While some missing information is OK (such as report date or severity score) other information is absolutely essential (bounty price, company name, severity <i>rating</i>, weakness type, etc).

I wrote a python script (`prune-empty-rewards.py`) to search for rows with critical missing data and remove them from the dataset. After this step, **I ended up with 1342 rows of clean data.**


### 2. Dealing with non-critical missing data ###
The other fields that were sometimes missing were non-critical meaning that the ML algorithm should still be able to make a fairly accurate decision. Perhaps, it wouldn't be as accurate as if it were with this data present, but it wouldn't skew the training or become an outlier. 

For these fields, the key to success was selecting a consistent "No value" placeholder that ML algo can learn as a signle separate categorical option. I had to be careful not to introduce multiple categorical options that meant the same thing, because that would certainly confuse the algorithm.

To accomplish this, I wrote a script (`fix-nans.py`) to find instances where fields were missing in different forms (such as '---' or '-' or empty) and replace them with a single consistent 'No value' placeholder.


### 3. Enriching the Data ###
I wanted to supplement my data with additional information for accuracy.

From my prior experience with estimating bug bounties, I knew that **company's size and location were often considerable factors** that played into the bug bounty price. 

To add this information, I wrote a script (`enrich-data.py`) that used APIs: 
  - Crunchbase API (to get basic company data)
  - Companies API (to get revenue and location data)
  - Google Maps API (to lash the location to city/state/country consistently)

This allowed me to have a much richer dataset that consisted of:
  - Company Name
  - Company Size
  - Company Revenue
  - Company Location (City, State, Country)
  - Bounty Awarded ($$$)
  - Bounty Weakness (i.e. SQL Injection)
  - Bounty Report Title (Text)
  - Bounty Report Description (Text)
  - Severity Rating (Low, Medium, High, Critical)
  - Severity Score (0-10)
  - Report Date
  - URL

### 4. Analyzing the Data ###
**Open-Source data:** 

While looking at the data and the corresponding bounty payouts, I realized that there was a significant discreptency between Open Source Projects/Communities and For-Profit Organizations. The Open-Source projects often provided lower payouts for the same types/severity of vulnerability. 

I decided to manually label those projects as "Open Source", thus introducing a new binary column into my dataset. This way, my ML algorithm would take this into account and hopefully be more accurate in its decision making.

**Dates:** 

Another caviat is the representation of dates in ML dataset. After reading [this article](https://towardsdatascience.com/machine-learning-with-datetime-feature-engineering-predicting-healthcare-appointment-no-shows-5e4ca3a85f96), I decided to explode each date into separate categorical columns: Year, Month, Day, Min - that would help ML algo create better associations/decisions in the process. I wrote a script that went through my entire dataset and converted the date into these categorical columns: `explode-dates.py` script.

**Binarization:** 

Since we're dealing with a lot of categorical data, as long as the number of variations for each feature is not overwhelming, it is best to binarize each variation, so that decision trees have a way at analyzing which variations were important. I accomplished it using `pd.get_dummies` and passing it the specific columns I wanted to binarize, leaving out the `Description` column, which had to be handled differently, as otherwise, all of its values would be unique.


### 5. Machine Learning Methods & Error Analysis ###
**Price Ranges:** 

After running some preliminary results using just default Decision Trees, I noticed that I was getting very poor results (~13% accuracy). I went back to analyzing my data and wrote a script `analyze-bounties.py` to see how many unique bounty prices I have. I ended up with 235 different bounty prices (target labels) across a 1342-row dataset. The variety of target labels here is quite vast across a rather small dataset, so no wonder the accuracy is poor. 

Instead, I decided to split my bounty prices into ranges:
  - `$0-1000`
  - `$1000-2000`
  - `$2000-5000`
  - `$5000-10000`
  - `$10000 plus`

This way instead of 135 target labels, we only have 5, while still making it a usable MVP product for users.

This significantly improved the accuracy of decision trees to over 50%. 

**Vectorizing the Description (Tfidf vs Count):** 

I tried using both, <b>tf-idf</b> and <b>count</b> vectorizers on description to see how they perform. While they both transform text into numeric form useful for machine learning models, the CountVectorizer simply produces the frequency of each token with respect to the index in the vocabulary. However, the **TfidfVectorizer hints at the overall originality** of the word by counting how many times it appears in the document vs the number of documents that token appears in.

I visualized the decision tree diagrams at multiple maxdepths for both vectorizers and found that in the case of using plain CountVectorizer, the tree tends to overfit right away, as I see some leafs containing company-specific terms from description like "dropbox" for example. Using tfidf produced much more original results and slightly better accuracy (by ~0.05).

**Decision Tree Tuning:**

At first attempt, I used the `DecisionTreeClassifier` without any params and it performed quite poorly (0.58 accuracy). It was clearly overfitting, because the training set accuracy was 1. To fix this, I decided to go the pre-prunning route and restrict the maximum depth of the tree to 3 or 4. 
To see what was happening with the tree exactly, I found a `graphviz` library I could use to save the tree to a .dot file and plot it visually.

- **With depth=3**, our trainset accuracy dropped to 0.695, but our test accuracy improved significantly from 0.58 -> to 0.6965, which told to me that it is overfitting much less over train data than it was before. 
Inspecting the tree tests visually, the decision chain made sense:
1. First, it started with checking whether severity is over 9.5 (since this immediately drops us into a much larger category of bounties).
2. If severity score was less than 9.5, the next test it chose was to see if the severity <i>rating</i> was higher than Low. This also makes sense, as it's now testing the lower bound to see just how low the bug severity is.
3. If severity score was 9.5 or higher, then the follow-up tests included checking the Description for important clues as to what type of vulnerability it is. For example, in one of the tests, it's checking for `__priveleg` hinting at the fact that when Privilige escalation has occured, it warrants the highest payout label.
(Refer to the diagram for the full tree visualization).

- **With depth=4**, I then decided to try depth=4, which would make the tree more complex, possibly give us a higher score, but may overfit more. The trainset accuracy improved to 0.71, while the test accuracy dropped from 0.695 (at depth=3) -> to 0.683. This immediately hints at overfitting from depth=3, since the test score went down, while train score went up. 
I decided to look at the visual tree just to see what it came up with, and as expected, we see that at level 4 the tree starts making decisions off terms like "dropbox" and "summary", which are not really important in the overall decision making about bug bounty price or severity. 
<br></br>

**Bringing it Together Using Pipeline**:

I wanted to join the results of my vectorized description with the results of Decision Tree classifier on other fields. This way, the Decision Tree takes into account all binarized features, together with tfdif'd description features. 

I was able to find a `make_pipeline` function that allowed me put it all together like this:
```
tree = DecisionTreeClassifier(max_depth=maxdepth, random_state=42)
ct1 = make_column_transformer((cv_desc, 'Report Description'), remainder='passthrough')
pipeline = make_pipeline(ct1, tree)
pipeline.fit(train_X, train_Y)
```


This performs column vectorization transformation over Description, while allowing other columns to 'passthrough' to the DecisionTreeClassifier without change. Then, decision tree takes them all together and analyzes.
<br></br>
### 6. Future Improvements ###

- Get more data (5000-10000 records)
- Look into joining `Weakness` and `Title` into the Pipline, along with Description
- More detailed tuning with Random Forest classifier
- Try post-pruning techniques instead of pre-pruning

