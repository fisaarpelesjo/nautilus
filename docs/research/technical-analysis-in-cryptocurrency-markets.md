# Technical Analysis In Cryptocurrency Markets

Source PDF: technical-analysis-in-cryptocurrency-markets.pdf

---

Technical Analysis in Cryptocurrency Markets: Do
      Transaction Costs and Bubbles Matter? ∗

          Daniel Svogun † Walter Bazán-Palomino ‡§

          svogun@cua.edu                wn.bazanp@up.edu.pe

          This version: February 10, 2022

                                                      Abstract

    The study of technical analysis in cryptocurrencies has largely ignored the
implications of often high transaction costs and bubble periods on trade rule
performance. We study the daily and 1-minute returns of 69 technical trade rules
in the form of moving average and breakout strategies, with and without transaction
costs, during price bubbles in the 2016-2021 period. For the most proﬁtable trade rules,
we ﬁnd that bubble periods increase the likelihood that Ethereum, Ripple and Litecoin
beat buy-and-hold, but not Bitcoin and Bitcoin Cash. Transaction costs decrease this
likelihood for Ripple and Litecoin, but increase it for Bitcoin and Ethereum.

JEL Classiﬁcation : G14, G20, G30, G32

Keywords  : Technical analysis, cryptocurrency, transaction costs, asset bubbles

    ∗We thank Flavio Abanto for research assistance. We gratefully acknowledge the ﬁnancial support of the Research

Center at Universidad del Pacíﬁco (CIUP) and the Busch School of Business at the Catholic University of America.

We alone are responsible for the views expressed in this paper and for any remaining errors.
    †The Busch School of Business, The Catholic University of America, Washington DC, USA Corresponding author:

Daniel Svogun Phone: +1-401-569-7184
    ‡School of Economics and Finance, Universidad del Pacíﬁco (Lima, Perú).
    §Center for International Policy Studies, Fordham University, New York, USA.


---

1 Introduction

Cryptocurrencies are a very risky new asset class, and investors spend time to understand their
price trends in order to proﬁt as a reward for that risk. To make money, investors aim to create
trend trading rules or strategies based on technical analysis to respond quickly to price changes,
either between days or within a day. A new strand of the cryptocurrency literature has explored
the proﬁtability of technical trading rules, ﬁnding positive returns with Bitcoin (Miller et al., 2019;
Corbet et al., 2019; Gerritsen et al., 2020) and other major cryptocurrencies (Grobys et al., 2020;
Ahmed et al., 2020). Their results might be evidence of ineﬃciency in crytocurrency markets, and
challenge the weak form of the eﬃcient market hypothesis (EMH). However, most of the previous
literature has not adjusted their proﬁts by transaction costs, and has not studied the impact of
bubble periods on the proﬁtability of technical trading rules. We aim to close this gap in the
literature.

This paper studies the impact of transaction costs and bubble periods on the returns of technical
trading rules in cryptocurrency markets. To that end, we ﬁrst extend and complement the
most recent literature on technical trading analysis in cryptocurrency markets by applying 69
parameterized trading rules from Corbet et al. (2019), Gerritsen et al. (2020), and Grobys et al.
(2020) to Bitcoin (BTC), Ethereum (ETH), Ripple (XRP), Litecoin (LTC), and Bitcoin Cash
(BCH), from 2016 to 2021. In particular, we calculate 69 trading returns, with and without
transaction costs, in the form of moving average and breakout strategies in the 1-minute and 1-day
frequency. The idea behind this approach is to assess whether there is a signiﬁcant decrease in the
number of trading rules producing positive proﬁts after adjusting by transaction costs (details in
the next section).

According to the EMH, investors cannot make proﬁts above the buy-and-hold (BH) strategy using
any technical trading rule that depends on past asset price patterns, because current prices already
reﬂect all information. On this matter, we study the probability that a trading strategy produces
higher returns than the buy-and-hold rule by employing a logistic regression model. That is, we
examine whether the chances of having an excess return – the return of a particular trade strategy
minus the buy-and-hold return – can be explained by transaction costs and bubble periods. We
identify bubble periods by applying the Phillips et al. (2015) (PSY) method. Moreover, we examine
whether the impact of transaction costs on the the odds ratio is stronger during bubble periods
(interaction terms). It is worth mentioning that, while we study trading rules that produce positive
proﬁts adjusted by transaction costs and the chances of having an excess return, we do not aim
to prove the existence of market ineﬃciency. However, market ineﬃciency and excess return by
applying trading rules might be related1.

This paper contributes to the growing literature on trading rules in cryptocurrency markets in
several ways. First, previous literature has used either daily (Ahmed et al., 2020; Gerritsen et al.,
2020; Grobys et al., 2020) or intraday (Miller et al., 2019; Corbet et al., 2019) data without
transaction costs. We close this gap in the literature by calculating trading returns with transaction
costs in both the 1-minute and 1-day price frequency. Second, although cryptocurrency markets
have experienced bubbles (Cheah and Fry, 2015; Corbet et al., 2018; Geuder et al., 2019; Cagli,

    1For further details on cryptocurrency market ineﬃciency, readers are referred to Zhang et al. (2018) and Al-
Yahyaee et al. (2018), and to the references therein.

                                                              1


---

2019; Bouri et al., 2019), their eﬀects on trading proﬁts have not been studied yet. By formally
examining the bubbles’ eﬀects on the probability of getting excess return, we also complement the
literature of both bubble periods and technical analysis in cryptocurrency markets. Third, contrary
to studies that only analyze Bitcoin (Miller et al., 2019; Corbet et al., 2019; Gerritsen et al., 2020),
we study the performance of trade rules for the most traded cryptocurrencies. In this regard, we
complement the few studies examining trading strategies employing daily price data on the most
traded cryptocurrencies (Grobys et al., 2020; Ahmed et al., 2020). Fourth, in considering the less
frequently studied 1-minute time frequency, we contribute to understanding the relevance of the
time frequency of the trading strategies since Dempster and Jones (2001) ﬁnd that price frequency
can dramatically vary technical trading proﬁts in the Forex market.

This paper oﬀers some important insights into the understanding of adjusted returns, i.e., trading
returns including transaction costs. Our results show that the number of proﬁtable trading rules
decrease after adjusting by transaction costs. However, we provide evidence that some rules can still
produce positive adjusted returns in both the 1-minute and 1-day time frequency. With respect to
excess returns with transaction costs, there are more trade rules producing positive excess returns
in the 1-day time frequency compared to the 1-minute frequency. To the best of our knowledge,
there is no other cryptocurrency research comparing adjusted returns and excess returns in the
1-minute and 1-day frequency. With reference to positive proﬁts beyond buy-and-hold without
transaction costs, our intraday and daily results are in line with previous studies (Miller et al.,
2019; Corbet et al., 2019; Gerritsen et al., 2020; Grobys et al., 2020; Ahmed et al., 2020).

On the question of the probability of having excess returns, we demonstrate with a subset of the
ﬁve most proﬁtable strategies for each cryptocurrency2 that transaction costs and bubble periods
matter. In particular, transaction costs increase the odds ratio of excess return for Bitcoin and
Ethereum, but decrease it for Ripple and Litecoin. Regarding bubble periods, we ﬁnd that this
variable increases the odds ratio of excess return for Ethereum, Ripple, and Litecoin, but it does
not have any eﬀect on the odds ratio for Bitcoin. Surprisingly, neither transaction costs nor bubbles
have any inﬂuence on the chances of having excess returns for Bitcoin Cash.

The rest of the paper is organized as follows. Section 2 describes the methodology we use, section
3 presents the data and discusses the results, and section 4 concludes.

2 Methodology

2.1 Detecting Bubbles

Identifying bubble periods in each cryptocurrency price series is a key ingredient in the analysis
of the performance of trading rules. Since cryptocurrencies lack intrinsic value (Cheah and Fry,
2015; Cheung et al., 2015; Klein et al., 2018; Huang et al., 2019), the dating algorithm of Phillips
et al. (2015) (PSY) is used to overcome the asset bubble deﬁnition based on fundamental value.
PSY propose a Generalized Supremum Augmented Dickey–Fuller (GSADF) test which is based on

    2We select these top-5 rules via a process described below.

                                                              2


---

a rolling-window ADF-style regression:

     p

xt = αr0w + αr1wxt−1 + φirw∆xt−i + εt,                                 (1)

     i=1

where xt is the cryptocurrency price; αr0w, αr1w, and φirw are parameters estimated using OLS; p is
the number of lags; εt is the innovation; and rw = r2 − r1 is a rolling window that starts and ends
respectively with a fraction r1 and a fraction r2. The null hypothesis states that the time series
xt has a unit-root (H0 : αr1w = 1), while the alternative hypothesis states that xt is an explosive
process (Ha : αr1w > 1). The GSADF test statistic is GSADF (r0) = supr2∈(r0,1) SADFr2(r0), where
SADFr2(r0) = supr2∈(r0,1) ADF0r2, and the asymptotic critical values are obtained from Monte
Carlo simulation with 2000 replications.

After the GSADF test detects explosive price behavior, the following date-stamping strategy is
used. For instance, the ﬁrst observation on which the backward GSADF statistic is greater than
the critical value is the start date of a bubble. Likewise, the ﬁrst observation after that start date
on which the GSADF statistic goes below the critical value is the end date of a bubble. Subsequent
bubbles can be identiﬁed similarly.

2.2 Technical Analysis Methodology

Corbet et al. (2019), Gerritsen et al. (2020), and Grobys et al. (2020) apply common technical
trading rules to cryptocurrency markets, generally focusing on Bitcoin, the ﬁrst cryptocurrency
in the market. Following the Neftci (1991) insight that the most fundamental kind of technical
trading rules are those that consider averages and extrema, we apply the Moving Average (MA)
and Breakout (BO) trade rules, to ﬁve cryptocurrencies in both the 1-minute and 1-day time
frequency. These rules are among the most well-studied in technical analysis, and we use common
parameterizations, several of which are studied in all three papers cited. Tables 1 and 2 specify the
trading rules and labels each with the paper(s) from which we cite it.

The ﬁrst, and perhaps single most well-studied technical analysis trade rule type is the Moving
Average (MA). Generally, there is a short-run MA (M AS), a long-run MA (M AL), and some band
length (band) where band = bandparam × M AL. Following the parameterizations in the studies
cited above, we use a bandparam of either 0 or 0.01 here. When M AS > M AL ± band, the trade
rule provides a “buy” signal, and a “sell” signal otherwise. Our notation closely follows the Corbet
et al. (2019) approach:

S                                       L

M AS = Pt−(n−1)/S > M AL = Pt−(n−1)/L + band ⇒ buy signal at time t,   (2)

n=1                                     n=1

S                                       L

M AS = Pt−(n−1)/S < M AL = Pt−(n−1)/L − band ⇒ sell signal at time t,  (3)

n=1                                     n=1

                                             3


---

The MA rule is fully deﬁned by its M AS, M AL and band lengths. The parameterizations of each
rule used is fully deﬁned in Table 1.

The second trading rule we use is of the Breakout (BO) rule type. The BO rule is deﬁned in the
following manner:

Pt > max(Pt−1, ..., Pt−n) + band ⇒ buy at time t,   (4)

Pt < min(Pt−1, ..., Pt−n) − band ⇒ sell at time t,  (5)

where the band is diﬀerent for the buying and selling signals. Here, in the buying signal, band =
max(Pt−1, ..., Pt−n) × bandparam, while for the selling signal, band = min(Pt−1, ..., Pt−n) × bandparam.
Similarly to the MA rules, we follow the parameterizations in the studies cited above, and use a
bandparam of either 0 or 0.01.

For the purposes of this study, the BO trading rule is fully deﬁned by the length of time n over which
an extreme value is compared to price in time t and the size of its bandparam. The parameterizations
of each rule used is fully deﬁned in Table 2.

We use 69 total parameterized trade rules of the MA and BO type for this study. These are
constructed by pooling all the rules of MA and BO type that are tested in Corbet et al. (2019),
Gerritsen et al. (2020), and Grobys et al. (2020), with the exception of two BO rules with
BOL = 1440. This BOL is not included because it would require close to 4 years of price data
before trading in the daily time frequency, nearly the size of some of our full data sets. To maintain
consistency, we do not test the BOL = 1440 rules in the 1-minute time frequency either.

2.3 The role of bubble periods and transaction costs

Having identiﬁed bubble periods by the PSY method and deﬁned each trade rule, we follow Bouri
et al. (2019) to study the role of bubble periods in the excess return time series (the percentage
trading period return of a particular trade strategy minus the percentage trading period return of
buy-and-hold). To that end, we employ the logistic regression model:

p(Y = 1|X)                                          (6)
log 1 − p(Y = 1|X) = β0 + β1D,

where the dependent variable Y is a dummy variable that takes the value of one when a trade rule
return is greater than the buy-and-hold return and zero otherwise, β0 is the intercept, and D is a
dummy variable that equals 1 for a bubble period and 0 otherwise.

One central aspect of the multiple logistic models is the estimation of the coeﬃcients and testing
for their signiﬁcance. If bubble periods increase the likelihood that a trading strategy produces
higher returns than the buy-and-hold rule, then β1 would be statistically signiﬁcant and positive.

                                4


---

Similarly, we study the impact of both transaction costs (X1) and bubble periods (D) on the odds
ratio, and investigate if transaction costs have a strong eﬀect on the odds ratio during bubble
periods (i.e. the interaction term β2):

p(Y = 1|X)                                                         (7)
log 1 − p(Y = 1|X) = β0 + φD + β1X1 + β2X1 × D.

If there is no diﬀerence in the impact of transaction costs during the bubble periods, we expect
that β2 is close to zero or is statistically insigniﬁcant.

Finally, we control for volume of transactions (X2) in the multivariate logistic regression model:

p(Y = 1|X)                                                         (8)
log 1 − p(Y = 1|X) = β0 + φD + β1X1 + β2X1 × D + β3X2 + β4X2 × D.

As in the previous cases, if volume of transactions increases the probability that a trading strategy
produces higher returns than the buy-and-hold rule, then β3 would be statistically signiﬁcant and
positive. In addition, we are interested in the interaction terms between transaction costs and
bubble periods (β2), and between volume of transactions and bubble periods (β4). That is, we
examine whether the eﬀect of transaction costs (volume of transactions) is diﬀerent among bubble
and non-bubble periods.

We run all three logistic models with all rules studied in each cryptocurrency. A summary of all
results, with more details for the ﬁve best performing trade rules is described below.

3 Results

3.1 Data and trading rules

Our dataset consists of 1-minute and daily cryptocurrency prices of Bitcoin (BTC), Ethereum
(ETH), Ripple (XRP), Bitcoin Cash (BCH), and Litecoin (LTC) measured in U.S. dollars,
for the period January 1, 2016 – November 10, 2021 (or the earliest available), sourced from
CryptoDataDownload.com. We work with these cryptocurrencies due to the time length of data
availability, in part because a wider time span allows us to test for bubbles. As of writing, they
account for about two-thirds of cryptocurrency market capitalization. Additionally, they are among
the most liquid digital monies – a necessary condition for technical trading strategies to work.
Transaction cost data is sourced from coinmetrics.io. Transaction costs here refer to the sum of all
fees paid to miners, transaction validators, stakers and/or block producers divided by the number
of transactions during a particular interval of time. Future research might break transaction cost
down on a more granular basis, using individual transactions on the blockchain, but we believe this
data is at least suﬃcient for initial transaction cost consideration. For the purpose of this research,
we calculate trading strategy proﬁts by their continuously compounded rate of return. Let Pi,t be
the price of cryptocurrency i at time t, and ri,t = lnPi,t − lnPi,t−1 be the logarithmic return.

            5


---

Table 3 presents a comparison of all 69 trade rules in the 1-minute price frequency with the buy-
and-hold return (holding the cryptocurrency from the ﬁrst period to the last), where the number of
trading rules greater than the buy-and-hold return each year are reported. Each column corresponds
to a speciﬁc cryptocurrency, where the superscript u refers to unadjusted or the trading returns
that do not include transaction costs, and the superscript a refers to adjusted or the trading returns
that include transaction costs. To understand this table it is better to present an example. The
number 52 in the ﬁrst column means 52 out of 69 trading strategies for Bitcoin, not including
transaction costs, produce better returns than the buy-and-hold rule. Likewise, the number 29 in
the second column refers to 29 out of 69 trading strategies for Bitcoin, including transaction costs,
that produce better returns than the buy-and-hold rule.

Table 3 shows, as expected, that there are more unadjusted trading strategies than adjusted trading
strategies that outperform the buy-and-hold rule in the 1-minute period. Notably, for Bitcoin in
2016 and 2018, proﬁtable rules decrease from 52 to 29 and 59 to 32, respectively. The ﬁnding that
some intraday Bitcoin trading strategies, without including transaction costs, produce positive
proﬁts broadly supports the work of other studies in this area (Miller et al., 2019; Corbet et al.,
2019).

In Ethereum, a more pronounced (by proportion) decrease happened in 2019 because 20 proﬁtable
rules become 5, after the inclusion of transaction costs. In the majority of cases, besides Litecoin,
the inclusion of transaction costs eliminates several instances of proﬁtability. However, as time
passes, in particular, in 2020 and 2021, this diﬀerence is not as substantial. The most interesting
aspect of this table is that there are some trading strategies including transaction costs that produce
proﬁts beyond the buy-and-hold rule.

The results of the trading rules at the daily time frequency are shown in Table 4. Similar to the
1-minute results, there are more unadjusted trading strategies than adjusted trading strategies that
outperforms the buy-and-hold rule. Nevertheless, compared to the 1-minute results, the diﬀerence
is smaller. What stands out in the table is that the trading rules at the daily time frequency
perform substantially better than on the 1-minute time frequency. In the majority of cases, the
1-minute time frequency has less proﬁtable rules than the daily time frequency. The decrease in
proﬁtable rules when transaction costs are not included, to when they are, is substantially more
in the 1-minute time frequency. In other words, in the 1-day time frequency, the inclusion of
transaction costs sometimes does not decrease the number of trade rules producing proﬁts beyond
the buy-and-hold strategy at all, and most frequently by only one. The number of trade rules
outperforming the buy-and-hold rule, with and without transaction costs, did not change in 2020
and 2021 for Bitcoin, Ethereum, and Bitcoin Cash. The single greatest decrease by number is from
45 rules to 40 in 2016 in Litecoin.

Taken together, the results shown in Tables 3 and 4 are quite revealing in several ways. First, in
terms of returns with transaction costs, the superiority of the daily trade rules over the 1-minute
trade rules could be explained by the fact that the 1-minute strategies have substantially more
time periods during which to trade, and would tend to produce more trading as a result. Second,
also interesting to note is the year 2018, in the daily time frequency, when every rule, both with
and without transaction costs, returned greater than buy-and-hold. This is a period that was
characterized by a large decrease in prices, suggesting these trade rules can help investors avoid
such periods. Third, the number of daily trading rules including transaction costs that produce

                                                              6


---

proﬁts greater than the buy-and-hold strategy for each cryptocurrency decrease after 2018. Fourth,
it is worth noting that, in terms of daily trading rules without adjusting by transaction costs, our
Bitcoin results are in line with those of Gerritsen et al. (2020).

To the best of our knowledge, there is no other research showing that a particular trading strategy
can produce proﬁts beyond transaction costs in cryptocurrencies. We provide evidence, however, in
Ethereum, Ripple, and Bitcoin Cash, three of ﬁve cryptocurrencies, of a general decline in relative
proﬁtability from year 2019 to 2021. The implication of this interesting ﬁnding is in line with
recent literature suggesting that Bitcoin (Khuntia and Pattanayak, 2018; Vidal-Tomás and Ibañez,
2018; Sensoy, 2019) and other cryptocurrency markets (Tran and Leirvik, 2020) are becoming more
eﬃcient over time.

There is a question as to whether 1-minute trading frequency is even possible in several
cryptocurrencies. When trades are undertaken through the blockchain, without the intermediary
of an exchange, transactions often take several minutes, at minimum, to complete. Also, most data
besides prices are available on a daily as opposed to 1-minute frequency. In part for these reasons,
our risk-return and regression analysis focus on the daily results.

It is conceivable that these excess returns are a reward for investors bearing extra risk on a
return to risk basis. To explore this argument, we report Sharpe ratios using daily data. Table 5
reports the number of trade-rule Sharpe ratios greater than the buy-and-hold Sharpe ratio in each
cryptocurrency, with and without transaction costs. For example, in Bitcoin without transactions,
49 trade rules have a higher Sharpe ratio than buy-and-hold. The latter supports evidence in
Gerritsen et al. (2020) that found relatively high Sharpe ratios among technical analysis trade rules
in Bitcoin. We ﬁnd this is the case in several other important cryptocurrencies as well. These
ranks remain relatively stable even with the inclusion of transaction costs. In Bitcoin and Bitcoin
Cash, the number of superior Sharpe ratios does not change, while in Ethereum, it decreases by 3,
in Ripple by 4 and in Litecoin by 10. All in all, there is a substantial number of trade rules – more
than 50% of trade rules for Bitcoin, Ethereum, and Bitcoin Cash – that generate a superior Sharpe
ratio. A natural implication is that technical trade rules with relatively better reward to risk ratios
than buy-and-hold exist, with stronger evidence in three of the ﬁve cryptocurrencies studied.

3.2 Trade rule returns and bubble periods

3.2.1 The big picture: 69 trading strategies

Table A.1 in the appendix provides a general overview of the Equation (6) results, indicating
positive and negative coeﬃcients, where the dependent variable is the logit of the odds ratios of
excess return (beyond buy-and-hold). The independent variable is a dummy variable indicating the
presence of a bubble as identiﬁed by the PSY process detailed above. The immediately proceeding
columns indicate the number of trade rules with a positive or negative coeﬃcient, and the number
of rules with statistical signiﬁcance at the 10%, 5% and 1% level, respectively. The results presented
are for excess returns with transaction costs. The bubble coeﬃcient (β1) directions and statistical
signiﬁcance levels are identical for excess return with and without transaction costs in all ﬁve
cryptocurrencies.

At the 1% level of statistical signiﬁcance, there are no coeﬃcients that are negative. The Ethereum

                                                              7


---

logit regressions indicate a statistically signiﬁcant positive relationship between excess return and
bubbles in a little over a third of rules. In the Bitcoin case, we ﬁnd similar results, with over half
the rules having a statistically signiﬁcant relationship between excess return and the presence of
bubbles. In the Ripple case, the logit regressions show slightly less than a third of bubble coeﬃcients
that are positive and statistically signiﬁcant. In the Litecoin case, about two-thirds of the rules
exhibit a positive and statistically signiﬁcant bubble coeﬃcient. In the Bitcoin Cash logit regression
case, about one-quarter of trade rules have a statistically signiﬁcant and positive coeﬃcient.

Table A.2 summarizes the coeﬃcients directions of Equation (7): the bubble coeﬃcient, the
transaction cost coeﬃcient and the interaction term coeﬃcient. After performing 345 total
regressions (one Equation (7) for each cryptocurreny and trade rule), at the 1% level of statistical
signiﬁcance, we ﬁnd that there are only 5 total regressions with a negative bubble coeﬃcient, versus
116 total regressions with a bubble coeﬃcient that is positive. While there are a few exceptions,
the evidence still strongly suggests that bubbles matter for trade rule proﬁts, and most often in
a positive direction, with four of ﬁve cryptocurrencies having at least 18 positive and statistically
signiﬁcant at the 1% level bubble coeﬃcient trade rule regressions. Transaction cost coeﬃcients
are split almost evenly between positive and negative coeﬃcients with statistical signiﬁcance at the
10% level in Ripple, Litecoin and Bitcoin, but positive and statistically signiﬁcant at the 10% level
the majority of the time in Ethereum and Bitcoin Cash. Some Bubble-TC interaction coeﬃcients
are positive, the most notable of which is Litecoin with 24 that are statistically signiﬁcant at the
1% level.

Equation (8), which includes volume of transactions and a volume-bubble interaction term, is
qualitatively similar with respect to bubble and transaction cost coeﬃcients, with similar direction
and levels of statistical signiﬁcance to those reported in Table A.2. The results indicate that
neither volume nor volume-bubble interaction terms appear to be relevant. Tables summarizing
the direction and statistical signiﬁcance of coeﬃcients for Equation (8) are available upon request.

Due to space constraints and in order to focus more closely in on important top performing trade
rule parameterizations, we describe a process below to limit more detailed reporting to ﬁve trade
rules. This process helps us determine whether the statistical signiﬁcance of bubbles and transaction
costs coeﬃcients are indeed coming from the most proﬁtable trade rules, and shed some light on
the salient direction of transaction cost coeﬃcients given the conﬂicting pooled results.

3.2.2 The best strategies: top-5

In this section, we select ﬁve high performing rules in each cryptocurrency to describe in further
detail3. The selection criteria is as follows: ﬁrst, for each cryptocurrency, we order total return of
each trading strategy from the highest to the lowest, both adjusted and unadjusted by transaction
costs. Then, to make the analysis comparable between adjusted and unadjusted strategies, we
select the 10 highest of each of them. Finally, we select the 5 highest return strategies that are
repeated in both rankings. We do not assume that a technical analyst could know these highest
returning rules before the time period begins. Overall results summarized above indicate statistical
signiﬁcance with bubbles in an often signiﬁcant portion of technical trade rules.

    3More detailed summaries of all rules are available upon request.

                                                              8


---

To illustrate the interaction between bubbles and excess return, we plot the returns of the top
returning trade strategy, the buy-and-hold return and the bubble periods (shaded area) in Figure
1. As Figure 1 shows, most cryptocurrencies experience higher proﬁts in their top trade rule during
bubble periods. It is worth noting that most cryptocurrencies experience bubble periods between
October 2017 - January 2018 and October 2020 - March 2021. In Table 6, descriptive statistics
of the top ﬁve trade rules as deﬁned above are reported. As previously stated, Table 4 shows the
relatively few diﬀerences in excess returns with and without transaction costs. The sample means
here in Table 6 conﬁrm this, with average daily returns staying fairly steady with and without
transaction costs in the top-5 rules for each cryptocurrency.

Table 7 presents the Sharpe ratios by year for each cryptocurrency’s top-5 rules, as compared to
buy-and-hold returns. The rightmost two columns labeled “Full Sample” combine returns over the
full period. Noteworthy is that in every rule, and in every cryptocurrency, the top-5 trade rules
have a higher full sample Sharpe ratio than the buy-and-hold return. It is implied then that, in
most years and in most cryptocurrencies, the annual Sharpe ratio of a top-5 trade rule is higher
than that of the buy-and-hold strategy4. Noteworthy exceptions include rule 57 in 2016 Bitcoin,
and nearly all rules in 2016 Litecoin.

Table 8 shows the top-5 rule results of the logit estimates of Equation (6) on the bubble coeﬃcient.
It can be seen that bubble periods do not change the odds ratio of a trade strategy generating
higher return than the buy-and-hold return for Bitcoin, and all but one trade rule in Bitcoin Cash.
For the other cryptocurrencies, bubble periods have a strong eﬀect on the odds ratio, with 1%
statistical signiﬁcance in every trade rule except rule 55 for Litecoin.

Table 9 shows the results of the logit estimates of Equation (7). The bubble coeﬃcient results
support those reported in Table 8. All bubble coeﬃcients are positive and statistically signiﬁcant
at the 5% level for Ethereum, Ripple, and Litecoin (except for the trade rule 55), but not for
Bitcoin and Bitcoin Cash. Interestingly, for Ethereum, the interaction coeﬃcient (β2) of trade rule
6 is positive and statistically signiﬁcant at the 1% level. This suggests that for this rule transaction
costs matter very much during bubble periods. Regarding the interaction coeﬃcient (β2) of Bitcoin
Cash in trade rule 4, a note of caution is due here since this coeﬃcient is extremely high, even
though it is statistically signiﬁcant at the 1% level. A potential explanation is that Bitcoin Cash
had the lowest transaction costs of all ﬁve cryptocurrencies, thus even a small change could increase
the odds ratio5.

All cryptocurrencies, except Bitcoin Cash, have a transaction cost coeﬃcient with some statistical
signiﬁcance. Interestingly, the coeﬃcient directions are not consistent at the 5% level of statistical
signiﬁcance. For Ethereum, the positive coeﬃcient indicates that transaction costs increase the
chances to beat the buy-and-hold strategy. On the other hand, for Ripple and Litecoin (except
rule 41), the negative coeﬃcient implies that transaction costs lower the chance to produce proﬁts
beyond the buy-and-hold strategy. In the Bitcoin case, the top-2 rules’ results suggest that an
increase in transaction cost increases the likelihood that a particular trading rule produces higher
return than the buy-and-hold return.

    4It is interesting to note that top returning trade rules do not always have the highest Sharpe ratio, although
the ordering of returns and Sharpe ratios by rule are typically quite close. We leave a more detailed look at this
phenomenon to future research.

    5Typically, the Bitcoin Cash transaction cost is lower by an order of magnitude or more in each period.

                                                              9


---

The evidence presented in Table 9 implies that transaction costs play a role in both increasing and
decreasing the likelihood that a particular trading rule produces higher return than the buy-and-
hold return, depending on the cryptocurrency. It is possible that traders bid slightly higher trading
fees in Bitcoin and Ethereum at times when common technical indicators indicate proﬁtability.
Also, Table 9 reveals that the coeﬃcient of the interaction between transaction costs and bubble
periods is not statistically signiﬁcant at the 1% level, except in two cases. That is, typically, the
eﬀect of transaction costs is not diﬀerent among bubble and non-bubble periods.

To verify that transaction costs could be a relevant factor that explains the likelihood that a
particular trading rule generates a higher return than the buy-and-hold return, we control for
volume of transactions. The results of Equation (8) are available upon request. The volume of
transaction coeﬃcient is not statistically signiﬁcant for most of the regression equations, or has a
value of zero in the few cases that it is statistically signiﬁcant. The coeﬃcient of the interaction
between bubble periods and volume of transactions is not statistically diﬀerent from zero. These
two results together imply that Equation (8) is not relevant.

4 Closing remarks

Earlier studies of technical analysis in cryptocurrencies did not include transaction costs. We
have shown that they change proﬁtability dramatically in the 1-minute time frequency, but not
substantially in the daily time frequency. We have shown also that bubbles can increase the
probability that a trade rule including transaction costs produces proﬁts beyond the buy-and-
hold strategy. To our knowledge, this is the ﬁrst study which provides evidence that bubbles and
transaction costs play a major role in the proﬁtability of moving average and breakout strategies.

We have also studied a set of the top-5 trade rules in each cryptocurrency. Clearly, bubbles
matter to technical analysis proﬁt in Ethereum, Ripple and Litecoin. Our additional regressions
demonstrate that transaction costs are relevant as well. Transaction costs increase the probability
of having excess returns in the two most proﬁtable trade rules in Bitcoin and ﬁve most in Ethereum.
However, it decreases the chances of having excess returns in Litecoin and Ripple. In addition, this
subset of strategies allowed us to demonstrate that there is at least one trading strategy including
transaction costs – for each year and for the entire sample – that produces a higher Sharpe ratio
(risk-adjusted return) than the buy-and-hold strategy. Here, we contribute to the Gerritsen et al.
(2020) evidence, who found high Sharpe ratios in the technical trading of Bitcoin.

Further studies might look at other methods of determining bubbles, other less commonly studied
trade rules, transaction costs that vary based on a per transaction basis, and diﬀering methods of
risk-return measurement. The returns we demonstrate above buy-and-hold, even with transaction
costs, may be evidence for some ineﬃciency in cryptocurrency markets. Formal eﬃciency testing
methods are needed to further study this matter. We provide evidence for a positive relationship
between transaction costs and the probability of having excess returns in top rules of Bitcoin and
Ethereum. It is possible that higher transaction costs are the result of higher transaction demand
from traders using these trade rules. Further work is needed to fully understand this phenomena.
We believe that traders can learn from our results, particularly in times with substantial price
decline. For example, in 2018, a year when our cryptocurrencies declined substantially for much
of the year, all trading rules performed better than the buy-and-hold strategy. In cases where

                                                              10


---

regulators ﬁnd that excessive technical trading in cryptocurrencies contributes to a loss of welfare,
our evidence suggests that transaction costs alone may not be suﬃcient to prevent these from
occurring. A supply-and-demand responsive Tobin-style tax may help prevent welfare-reducing
technical trades further. Our results suggest that regulators ought to be particularly wary of excess
return rules in bubble periods.

References

Ahmed, S., Grobys, K., and Sapkota, N. (2020). Proﬁtability of technical trading rules among
   cryptocurrencies with privacy function. Finance Research Letters, 35:101495.

Al-Yahyaee, K. H., Mensi, W., and Yoon, S.-M. (2018). Eﬃciency, multifractality, and the long-memory
   property of the bitcoin market: A comparative analysis with stock, currency, and gold markets. Finance
   Research Letters, 27:228–234.

Bouri, E., Shahzad, S. J. H., and Roubaud, D. (2019). Co-explosivity in the cryptocurrency market.
   Finance Research Letters, 29:178–183.

Cagli, E. C. (2019). Explosive behavior in the prices of bitcoin and altcoins. Finance Research Letters,
   29:398–403.

Cheah, E.-T. and Fry, J. (2015). Speculative bubbles in bitcoin markets? an empirical investigation into
   the fundamental value of bitcoin. Economics Letters, 130:32–36.

Cheung, A., Roca, E., and Su, J.-J. (2015). Crypto-currency bubbles: an application of the phillips–shi–yu
   (2013) methodology on mt. gox bitcoin prices. Applied Economics, 47(23):2348–2358.

Corbet, S., Eraslan, V., Lucey, B., and Sensoy, A. (2019). The eﬀectiveness of technical trading rules in
   cryptocurrency markets. Finance Research Letters, 31:32–37.

Corbet, S., Lucey, B., and Yarovaya, L. (2018). Datestamping the bitcoin and ethereum bubbles. Finance
   Research Letters, 26:81–88.

Dempster, M. A. H. and Jones, C. M. (2001). A real-time adaptive trading system using genetic
   programming. Quantitative Finance, 1:397–413.

Gerritsen, D. F., Bouri, E., Ramezanifar, E., and Roubaud, D. (2020). The proﬁtability of technical trading
   rules in the bitcoin market. Finance Research Letters, 34:101263.

Geuder, J., Kinateder, H., and Wagner, N. F. (2019). Cryptocurrencies as ﬁnancial bubbles: The case of
   bitcoin. Finance Research Letters, 31.

Grobys, K., Ahmed, S., and Sapkota, N. (2020). Technical trading rules in the cryptocurrency market.
   Finance Research Letters, 32:101396.

Huang, J.-Z., Huang, W., and Ni, J. (2019). Predicting bitcoin returns using high-dimensional technical
   indicators. The Journal of Finance and Data Science, 5(3):140–155.

Khuntia, S. and Pattanayak, J. (2018). Adaptive market hypothesis and evolving predictability of bitcoin.
   Economics Letters, 167:26–28.

                                                              11


---

Klein, T., Thu, H. P., and Walther, T. (2018). Bitcoin is not the new gold–a comparison of volatility,
   correlation, and portfolio performance. International Review of Financial Analysis, 59:105–116.

Miller, N., Yang, Y., Sun, B., and Zhang, G. (2019). Identiﬁcation of technical analysis patterns with
   smoothing splines for bitcoin prices. Journal of Applied Statistics.

Neftci, S. N. (1991). Naive trading rules in ﬁnancial markets and wiener-kolmogorov prediction theory: A
   study of" technical analysis". Journal of Business, pages 549–571.

Phillips, P. C., Shi, S., and Yu, J. (2015). Testing for multiple bubbles: Historical episodes of exuberance
   and collapse in the s&p 500. International Economic Review, 56(4):1043–1078.

Sensoy, A. (2019). The ineﬃciency of bitcoin revisited: A high-frequency analysis with alternative
   currencies. Finance Research Letters, 28:68–73.

Tran, V. L. and Leirvik, T. (2020). Eﬃciency in the markets of crypto-currencies. Finance Research Letters,
   35:101382.

Vidal-Tomás, D. and Ibañez, A. (2018). Semi-strong eﬃciency of bitcoin. Finance Research Letters,
   27:259–265.

Zhang, W., Wang, P., Li, X., and Shen, D. (2018). The ineﬃciency of cryptocurrency and its cross-
   correlation with dow jones industrial average. Physica A: Statistical Mechanics and its Applications,
   510:658–670.

                                                              12


---

(a) Bitcoin returns  (b) Ethereum returns

(c) Ripple returns   (d) Litecoin returns

                  (e) Bitcoin Cash returns

Figure 1. Cryptocurrency returns and bubble periods. Trading strategies: Strategies including
transaction costs (solid blue line), and buy-and-hold (dashed black line). Bubble periods are
represented by shaded areas.

                                                              13


---

      Table 1. Technical Trade Rules: Moving Average.

M AS  M AL  bandparam  Paper        M AS  M AL  bandparam  Paper
1     5     0          A            2     150   0          A
1     5     0.01       A            2     150   0.01       A
1     10    0          A            2     200   0          A and B
1     10    0.01       A            2     200   0.01       A
1     20    0          A and C      5     20    0          A
1     20    0.01       A            5     20    0.01       A
1     50    0          A, B, and C  5     50    0          A
1     50    0.01       A            5     50    0.01       A
1     100   0          A and C      5     100   0          A
1     100   0.01       A            5     100   0.01       A
1     150   0          A, B, and C  5     150   0          A and B
1     150   0.01       A            5     150   0.01       A
1     200   0          A, B, and C  5     200   0          A
1     200   0.01       A            5     200   0.01       A
2     5     0          A            10    20    0          A
2     5     0.01       A            10    20    0.01       A
2     10    0          A            10    50    0          A
2     10    0.01       A            10    50    0.01       A
2     20    0          A            10    100   0          A
2     20    0.01       A            10    100   0.01       A
2     50    0          A            10    150   0          A
2     50    0.01       A            10    150   0.01       A
2     100   0          A            10    200   0          A
2     100   0.01       A            10    200   0.01       A

Notes: This table deﬁnes all trade rules used of the Moving Average (MA) rule type.
The short-hand for MA rules are as follows: MA(M AS, M AL, bandparam).

                       14


---

             Table 2. Technical Trade Rules: Breakout.

             BOL  Band  Paper      BOL  Band  Paper
             10   0     A          120  0     A
             10   0.01  A          120  0.01  A
             20   0     A          150  0     B
             20   0.01  A          180  0     A
             30   0     A          180  0.01  A
             30   0.01  A          200  0     B
             50   0     B          360  0     A
             60   0     A          360  0.01  A
             60   0.01  A          720  0     A
             90   0     A          720  0.01  A
             90   0.01  A

             Notes: This table deﬁnes all trade rules used of the
             Breakout (BO) rule type. The short-hand for these
             BO rules are as follows: BO(1, BOL, bandparam),
             where 1 represents that Pt is equivalent to a one-
             period average. “A” denotes the paper of Corbet
             et al. (2019), and “B” denotes the paper of Gerritsen
             et al. (2020).

Table 3. Trading strategies greater than buy-and-hold, 1-minute time frequency.

Year BT Cu BT Ca ET Hu ET Ha XRP u XRP a LT Cu LT Ca BCHu BCHa

2016 52  29  22   5     0          0    0     0                     0   0

2017 11  5   6    5     4          4    0     0                     6   6

2018 59  32  35   12    29         13   0     0                     31  30

2019 20  9   20   5     18         6    2     2                     7   6

2020 17  6   6    5     9          4    2     2                     5   5

2021 19  7   6    5     5          4    2     2                     5   5

Notes: Number of 1-minute trading strategies that performs better than the buy-and-hold rule.
The superscript u denotes a return of a trading strategy that does not include transaction cost,
the superscript a denotes a return of a trading strategy that includes transaction cost, and 0
means that there is no data for a particular cryptocurrency.

                               15


---

Table 4. Trading strategies greater than buy-and-hold, 1-day time frequency.

Year BT Cu BT Ca ET Hu ET Ha XRP u XRP a LT Cu LT Ca BCHu BCHa

2016 27  27  53  53          0       0   45  40                 0   0

2017 6   6   5   5           5       4   6   6                  35  35

2018 69  69  69  69          69      69  69  69                 69  69

2019 32  32  50  47          60      59  42  38                 25  25

2020 16  16  16  16          42      38  17  17                 18  18

2021 28  28  16  16          17      17  41  37                 18  18

Notes: Number of 1-day trading strategies that performs better than the buy-and-hold rule.
The superscript a denotes the adjusted trading return (with transaction costs), the superscript
u denotes the unadjusted trading return (without transaction costs), and 0 means that there is
no data for a particular cryptocurrency.

             Table 5. Number of trade rules with a
             Sharpe ratio greater than that of buy-and-
             hold, 1-day frequency.

             Cryptocurrency  No TC Rank  TC Rank
             BTC             49          49
             ETH             62          59
             XRP             30          26
             LTC             41          31
             BCH             47          47

             Notes: Daily Sharpe ratios for each rule’s return
             and buy-and-hold return were calculated and
             ranked. The number recorded indicates the
             number of trade rules with a Sharpe ratio greater
             than that of buy-and-hold. TC here is an acronym
             for transaction costs.

                                 16


---

Table 6. Descriptive Statistics of the top-5 trade rules and buy-and-hold (B-H) strategy.

                   Adjusted                                 Unadjusted

Index Mean Median Std. Skew. Kurt. Min Max Mean Median Std. Skew. Kurt. Min Max

          34 0.26  0.00 3.28 -0.05 7.46 -18.88 23.15 0.26   0.00 3.28 -0.05 7.46 -18.88 23.15
          33 0.25  0.00 3.28 -0.06 7.52 -18.88 23.15 0.25   0.00 3.28 -0.06 7.52 -18.88 23.15
BTC 12 0.25        0.00 3.31 -0.11 7.41 -18.88 23.15 0.25   0.00 3.31 -0.11 7.41 -18.88 23.15
          11 0.25  0.00 3.31 -0.11 7.44 -18.88 23.15 0.25   0.00 3.31 -0.11 7.44 -18.88 23.15
          57 0.25  0.00 3.36 -0.13 6.89 -18.88 23.15 0.25   0.00 3.36 -0.13 6.89 -18.88 23.15
         B-H 0.23  0.24 4.17 -0.47 6.88 -36.76 25.75

          40 0.39  0.00 4.43 0.21 9.92 -38.78 31.94 0.40    0.00 4.43 0.22 9.91 -38.78 31.94
          20 0.37  0.00 4.32 0.27 10.84 -38.78 31.94 0.39   0.00 4.31 0.28 10.85 -38.78 31.94
ETH 19 0.37        0.00 4.30 0.34 10.76 -38.78 31.94 0.39   0.00 4.29 0.35 10.81 -38.78 31.94
          51 0.36  0.00 4.39 0.15 10.17 -38.78 31.94 0.37   0.00 4.37 0.18 10.15 -38.78 31.94
           6 0.35  0.00 4.34 0.23 10.85 -38.92 31.94 0.37   0.00 4.32 0.27 10.86 -38.78 31.94
         B-H 0.31  0.23 5.76 -0.17 3.98 -38.78 31.94

          17 0.43  0.00 6.40 3.82 58.83 -65.30 102.80 0.47  0.00 6.38 3.86 59.39 -65.30 102.80
           4 0.41  0.00 6.39 3.82 59.23 -65.30 102.80 0.44  0.00 6.37 3.87 59.92 -65.30 102.80
XRP 18 0.40        0.00 6.21 3.83 64.12 -65.30 102.80 0.42  0.00 6.20 3.87 64.53 -65.30 102.80
           3 0.40  0.00 6.39 3.82 59.18 -65.30 102.80 0.44  0.00 6.36 3.89 60.25 -65.30 102.80
           5 0.38  0.00 6.37 3.75 59.93 -65.30 102.80 0.40  0.00 6.36 3.80 60.45 -65.30 102.80
         B-H 0.29  -0.05 7.80 1.85 28.11 -65.30 102.80

           6 0.25  0.00 4.40 2.51 26.69 -21.43 59.15 0.27   0.00 4.39 2.55 27.00 -21.07 59.15
          30 0.25  0.00 4.37 2.37 27.11 -23.42 59.15 0.26   0.00 4.36 2.38 27.24 -23.42 59.15
LTC 41 0.24        0.00 4.81 1.20 23.57 -45.59 59.15 0.24   0.00 4.81 1.20 23.60 -45.59 59.15
          55 0.23  0.00 4.85 1.17 22.71 -45.63 59.15 0.24   0.00 4.85 1.18 22.76 -45.59 59.15
           5 0.23  0.00 4.42 2.49 26.38 -21.43 59.15 0.26   0.00 4.40 2.54 26.84 -21.07 59.15
         B-H 0.19  0.00 5.85 0.47 12.81 -48.21 59.15

           5 0.17 0.00 4.58 1.67 20.04 -29.21 42.54 0.17    0.00 4.57 1.67 20.04 -29.20 42.54
           6 0.15 0.00 4.61 1.61 19.62 -29.21 42.54 0.15    0.00 4.61 1.61 19.62 -29.20 42.54
BCH 19 0.14 0.00 4.59 1.61 19.80 -29.21 42.54 0.14          0.00 4.59 1.61 19.80 -29.20 42.54
           4 0.13 0.00 4.44 2.06 21.18 -22.64 42.54 0.13    0.00 4.44 2.06 21.18 -22.64 42.54
          49 0.11 0.00 4.57 1.68 20.18 -29.21 42.54 0.11    0.00 4.57 1.68 20.19 -29.20 42.54
         B-H -0.10 -0.09 6.55 -0.24 11.46 -59.38 42.54

Notes: This table shows the descriptive statistics of the top-5 trade rules and the buy-and-hold (B-H) strategy
for each cryptocurrency, using daily data. Index denotes the Trade Rule Index.

                             17


---

Table 7. Sharpe ratio of the top-5 trade rules and buy-and-hold (B-H) strategy.

               2016  2017  2018      2019  2020  2021 Full Sample

Index A U A U A U A U A U A U A U

           34 1.75 1.75 2.59 2.59 -1.57 -1.57 1.40 1.40 2.31 2.31 1.30 1.30 8.90 8.91
           33 1.62 1.62 2.60 2.60 -1.53 -1.52 1.39 1.39 2.10 2.10 1.19 1.19 8.57 8.58
BTC 12 2.17 2.17 2.69 2.69 -1.42 -1.42 1.19 1.19 2.04 2.04 0.98 0.98 8.41 8.42
           11 2.29 2.29 2.69 2.69 -1.57 -1.56 1.21 1.21 2.04 2.04 0.89 0.89 8.33 8.34
           57 1.41 1.41 2.69 2.69 -1.59 -1.59 1.15 1.15 2.07 2.07 1.31 1.31 8.16 8.16
          B-H 1.70 1.70 2.69 2.69 -1.42 -1.42 0.87 0.87 1.94 1.94 0.89 0.89 6.21 6.21

           40 -0.21 -0.20 3.96 3.97 0.05 0.07 0.38 0.40 3.13 3.16 1.03 1.13 9.28 9.48
           20 -0.36 -0.34 3.82 3.83 -0.23 -0.20 0.39 0.41 2.55 2.69 1.71 1.87 9.05 9.41
ETH 19 -0.37 -0.35 3.75 3.77 -0.08 -0.03 0.50 0.53 2.08 2.30 1.89 2.06 9.04 9.51
           51 -0.61 -0.59 3.59 3.60 0.18 0.19 0.06 0.08 2.45 2.55 1.55 1.63 8.55 8.76
            6 -0.17 -0.15 3.82 3.84 -0.58 -0.53 0.42 0.44 2.21 2.42 1.64 1.86 8.55 9.05
          B-H -0.09 -0.09 3.39 3.39 -1.44 -1.44 -0.03 -0.03 1.96 1.96 1.60 1.60 5.58 5.58

           17        2.81 2.96 0.34 0.49 -1.02 -0.89 1.10 1.13 1.02 1.08 6.89 7.43
            4        2.81 2.89 0.01 0.17 -1.12 -1.02 1.06 1.09 1.05 1.12 6.60 7.03
XRP 18               2.67 2.76 0.06 0.19 -0.69 -0.59 0.93 0.95 1.13 1.18 6.57 6.95
            3        2.63 2.82 -0.02 0.19 -1.15 -1.00 1.46 1.51 0.93 1.01 6.38 7.08
            5        2.32 2.42 0.30 0.42 -0.67 -0.56 1.55 1.58 0.61 0.67 6.01 6.43
          B-H        2.53 2.53 -1.37 -1.37 -0.83 -0.83 0.11 0.11 0.99 0.99 3.38 3.38

            6 -0.13 0.46 1.81 1.93 -0.03 0.00 1.72 1.74 1.31 1.33 0.71 0.72 6.35 6.84
           30 -0.26 0.06 2.38 2.44 -1.10 -1.07 1.06 1.08 1.75 1.76 0.57 0.58 6.27 6.57
LTC 41 -0.05 0.19 2.33 2.35 -1.70 -1.68 1.24 1.24 1.45 1.45 0.17 0.18 5.46 5.61
           55 -0.35 -0.23 2.50 2.50 -1.62 -1.61 1.23 1.23 0.80 0.81 0.32 0.32 5.34 5.42
            5 -0.54 0.39 2.00 2.13 -0.29 -0.24 1.15 1.18 1.26 1.27 0.87 0.87 5.85 6.63
          B-H 0.42 0.42 2.50 2.50 -1.86 -1.86 0.29 0.29 1.04 1.04 0.34 0.34 3.58 3.58

            5              -0.15 -0.14 1.12 1.12 0.73 0.73 1.01 1.01 2.70 2.70
            6              -0.35 -0.35 0.98 0.98 0.80 0.80 0.92 0.92 2.29 2.30
BCH 19                     -0.35 -0.35 1.01 1.01 0.78 0.78 0.86 0.87 2.24 2.24
            4              0.17 0.17 -0.03 -0.03 -0.08 -0.08 1.64 1.64 2.09 2.09
           49              -0.11 -0.11 0.93 0.93 -0.29 -0.29 1.10 1.10 1.81 1.82
          B-H              -1.96 -1.96 0.28 0.28 0.46 0.46 0.37 0.37 -1.14 -1.14

Notes: This table reports the Sharpe ratio for the top-5 trade rules and the buy-and-hold (B-H) strategy for
each cryptocurrency, using daily data. Index denotes the Trade Rule Index, A denotes the Adjusted trading
return (with transaction costs), and U denotes the Unadjusted trading return (without transaction costs).

                                 18


---

Table 8. Equation (6) - Logit Regression Results of
the top-5 trade rules.

     Trade Rule Index             Trade Rule  Bubble (φ)
BTC
                                MA(1,150,0)         33.606
                         11   MA(1,150,.01)          33.33
                         12                         33.104
                         33     MA(5,100,0)         32.809
                         34   MA(5,100,.01)         33.792
                         57
ETH                             BO(1,60,.01)     3.926***
                           6                     3.911***
                         19    MA(1,20,.01)      3.514***
                         20      MA(2,20,0)
                         40                         2.6***
                         51    MA(2,20,.01)      4.583***
XRP                           MA(10,20,.01)
                           3                     2.251***
                           4      BO(1,20,0)     2.305***
                           5                     3.756***
                         17      MA(1,10,0)      2.036***
                         18    MA(1,10,.01)      2.084***
LTC
                           5     MA(1,20,0)      1.626***
                           6     MA(2,10,0)      1.679***
                         30    MA(2,10,.01)      1.456***
                         41                      4.251***
                         55      MA(1,20,0)
BCH                            MA(1,20,.01)         32.791
                           4   MA(5,20,.01)
                           5    MA(10,50,0)       2.36***
                           6                        32.206
                         19       BO(1,50,0)        33.532
                         49                         30.769
                               MA(1,10,.01)         31.348
                                 MA(1,20,0)

                               MA(1,20,.01)
                                 MA(2,20,0)
                                  BO(1,10,0)

Notes: This table reports the coeﬃcient results of Equation
(6) for the top-5 trade rules for each cryptocurrency, using
daily data. (*), (**), and (***) represent statistical
signiﬁcance at the 10%, 5%, and 1% levels, respectively.

                              19


---

Table 9. Equation (7) - Logit Regression Results of the top-5 trade rules.

     Trade Rule Index             Trade Rule  Bubble (φ) .     TC (β1)     Bubble ×TC (β2)
 BTC
                                MA(1,150,0)          32.379     0.052**                   -0.049
                         11   MA(1,150,.01)            32.36    0.053**                   -0.049
                         12                          33.169                               -0.028
                         33     MA(5,100,0)          33.326        0.032                  -0.029
                         34   MA(5,100,.01)          31.894        0.034                   0.009
                         57                                         -0.01
ETH                             BO(1,60,.01)        1.685**                          23.942***
                           6                        3.36***     0.021**                    0.264
                         19    MA(1,20,.01)       3.039***        0.017*                   0.187
                         20      MA(2,20,0)       2.627***                                -0.029
                         40                       5.122***      0.022**                   -0.082
                         51    MA(2,20,.01)                    0.037***
XRP                           MA(10,20,.01)         3.47***    0.036***               -116.406*
                           3                      3.526***                            -117.593*
                           4      BO(1,20,0)      2.725***    -30.274**
                           5                      2.834***    -29.087**                 550.498
                         17      MA(1,10,0)       2.886***    -24.038**                  -81.266
                         18    MA(1,10,.01)                   -31.127**                  -83.693
LTC                                               1.842***
                           5     MA(1,20,0)       1.839***       -28.7**                   0.933
                           6     MA(2,10,0)       1.634***                                   1.28
                         30    MA(2,10,.01)       4.315***    -2.898***                    0.991
                         41                                   -3.002***                      0.46
                         55      MA(1,20,0)          32.954   -2.772***                    1.547
BCH                            MA(1,20,.01)
                           4   MA(5,20,.01)      -9.795***        -1.216          3121.724***
                           5    MA(10,50,0)          32.691    -1.577**                    0.011
                           6                           34.98                               0.028
                         19       BO(1,50,0)         32.725        0.268                   0.094
                         49                          32.319       -0.012                   0.256
                               MA(1,10,.01)                       -0.034
                                 MA(1,20,0)                       -0.109
                                                                  -0.282
                               MA(1,20,.01)
                                 MA(2,20,0)
                                  BO(1,10,0)

Notes: This table reports the coeﬃcient results of Equation (7) for the top-5 trade rules for each
cryptocurrency, using daily data. (*), (**), and (***) represent statistical signiﬁcance at the 10%,
5%, and 1% levels, respectively.

                                              20


---

Appendix: Regression - All Strategy Summary

        Table A.1. Equation (6) - Logit Regression Results’ Summary.

             Coeﬀ. Value Times p-value<.1 p-value < .05 p-value < .01

Bitcoin

φ            (positive)  69      37          37                       37

             (negative)  0       0           0                        0

Ethereum

φ            (positive)  69      26          26                       26

             (negative)  0       0           0                        0

Ripple

φ            (positive)  69      22          22                       20

             (negative)  0       0           0                        0

Litecoin

φ            (positive)  69      52          52                       52

             (negative)  0       0           0                        0

Bitcoincash

φ            (positive)  67      16          16                       16

             (negative)  0       0           0                        0

Notes: This table reports the number of trade rules, including transaction costs, with
statistically signiﬁcant bubble coeﬃcient (φ) in the Equation (6). The column “Coeﬀ. Value”
indicates whether φ is positive or negative. The column “Times” indicates the number of times
that φ is either positive or negative.

                             21


---

Table A.2. Equation (7) - Logit Regression Results’ Summary.

Bitcoin      Coeﬀ. Value    Times    p-value<.1     p-value < .05      p-value < .01
      φ
                (positive)       67             37                37                 33
     β1         (negative)        2              0                  0                  0
     β2         (positive)       36             29
Ethereum        (negative)       33             24                28                 20
      φ         (positive)       10              1                16                   1
                (negative)       59              8                                     0
     β1                                                             0                  4
     β2         (positive)       69             40                  6
Ripple          (negative)        0              0                                   36
      φ         (positive)       69             61                40                   0
                (negative)        0              0                  0
     β1         (positive)       25             14                                   55
     β2         (negative)       44              8                57                   0
Litecoin                                                            0
      φ         (positive)       62             22                                   13
                (negative)        7              5                14                   4
     β1         (positive)       27             18                  6
     β2         (negative)       42             19                                   18
Bitcoincash     (positive)       45              8                18                   2
      φ         (negative)       24              6                  4
                                                                                     10
     β1         (positive)       47             28                15                   0
     β2         (negative)       22              4                12                   8
                (positive)       38             30                                     0
                (negative)       31             24                  8
                (positive)       49             24                  4                28
                (negative)       20              0                                     0
                                                                  28
                (positive)       63              4                  2                30
                (negative)        4              3                30                 15
                (positive)       54             37                19                 24
                (negative)       13              0                24
                (positive)       24              3                  0                  0
                (negative)       43              0
                                                                    4                  1
                                                                    3                  3
                                                                  37                 37
                                                                    0                  0
                                                                    3                  3
                                                                    0                  0

Notes: This table reports the number of trade rules, including transaction costs, with
statistically signiﬁcant bubble coeﬃcient (φ) in the Equation (7). The column “Coeﬀ. Value”
indicates whether φ (β1 or β2) is positive or negative. The column “Times” indicates the
number of times that φ (β1 or β2) is either positive or negative.

                                     22


---


