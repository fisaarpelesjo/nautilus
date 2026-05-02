# The Profitability Of Technical Trading Rules In The Bitcoin Market

Source PDF: the-profitability-of-technical-trading-rules-in-the-bitcoin-market.pdf

---

                                Finance Research Letters 34 (2020) 101263
                               Contents lists available at ScienceDirect

                         Finance Research Letters

                     journal homepage: www.elsevier.com/locate/frl

The profitability of technical trading rules in the Bitcoin market

                                                                                                                              T
Dirk F. Gerritsena, Elie Bourib, Ehsan Ramezanifarc,d,⁎, David Roubaude

a Utrecht University School of Economics, Utrecht, the Netherlands
b USEK Business School, Holy Spirit University of Kaslik, Jounieh, Lebanon
c Utrecht University School of Economics, Utrecht, the Netherlands
d Open University, School of Management Science & Technology, Heerlen, the Netherlands
e Montpellier Business School, Montpellier, France

ARTICLE INFO         ABSTRACT

Keywords:            We apply seven trend-following indicators to assess the profitability of technical trading rules in
Technical analysis   the Bitcoin market. Using daily price data from July 2010 to January 2019, our main results show
Trading rules        that specific technical analysis trading rules, mainly trading range breakout, contain significant
Profitability        forecasting power for Bitcoin prices, allowing the outperformance of the buy-and-hold strategy
Excess return        through the Sharpe ratio computed via the bootstrapping method. Results from various sub-
Bitcoin              periods, representing normal and boom markets, generally confirm our main finding and show
                     that the added value of the trading range breakout rule delivers outperformance in strongly
JEL classification:  trending markets.
C22
G10

1. Introduction

    Bitcoin has emerged as a leading digital currency and an investment destination, offering investors a novel investment oppor-
tunity (Dyhrberg, 2016; Bouri et al., 2017). The lack of intrinsic valuation methods for Bitcoin has led many traders to explore the
predicting power of exogenous variables such as Bitcoin popularity and attention (Kristoufek, 2015; Dastgir et al., 2019), trading
volume (Blacilar et al., 2017), hashing difficulty (Hayes, 2017), other cryptocurrencies (Bouri et al., 2019; Ji et al., 2019), geopo-
litical risks (Aysan et al., 2019), economic uncertainty (Demir et al., 2018), stock market uncertainty (Bouri et al., 2017), and energy/
commodity prices (Hayes, 2017; Bouri et al., 2018). Importantly, Bitcoin prices seem not to take an unpredictable path but to exhibit
inefficiency instead (Tiwari et al., 2018), possibly emanating from its short history and the irrational behaviours of its market
participants (Bouri et al., 2019). However, prior studies regarding the efficiency of Bitcoin assess predictability based on a departure
from a random walk (e.g., Tiwari et al., 2018), without offering any practical inferences for the sake of Bitcoin traders. Furthermore,
the extent to which technical trading rules perform when applied to Bitcoin prices remains unclear.1

    In this study, we examine whether technical trading rules can outperform a buy-and-hold strategy in the Bitcoin market. We apply
seven trading rules (Gerritsen, 2016) and evaluate their performance with three strategies based on the Sharpe ratio computed via the
bootstrapping method of Ledoit and Wolf (2008).

    Our examination provides Bitcoin traders with a more practical trading exercise based on trading rules, which helps Bitcoin
traders in making trading and investment decisions. It also extends the literature dealing with the predictability and efficiency of

  ⁎ Corresponding author.
    E-mail addresses: d.f.gerritsen@uu.nl (D.F. Gerritsen), eliebouri@usek.edu.lb (E. Bouri), e.ramezanifar@uu.nl (E. Ramezanifar),

d.roubaud@montpellier-bs.com (D. Roubaud).
  1 The ability of technical trading rules to generate excess return is often interpreted as evidence against market efficiency.

https://doi.org/10.1016/j.frl.2019.08.011
Received 18 April 2019; Received in revised form 31 July 2019; Accepted 12 August 2019
Available online 13 August 2019
1544-6123/ © 2019 Elsevier Inc. All rights reserved.


---

D.F. Gerritsen, et al.                                                                                                     Finance Research Letters 34 (2020) 101263

Bitcoin (e.g., Tiwari et al., 2018).
    Our main results show that the trading range breakout rule consistently delivers higher Sharpe ratios than a buy-and-hold strategy

for the full sample period and during periods of strongly trending markets. Other technical trading rules do not outperform the buy-
and-hold strategy.

    The rest of the paper is divided into three sections. Section 2 describes the method and data. Section 3 presents the estimation
results for the full sample and subsamples. Section 4 concludes.

2. Method and data

2.1. Technical trading rules

    Following Gerritsen (2016), we discuss seven families of trading rules which were well-publicized prior to the start of exchange
trading of Bitcoin. The fact that we test commonly known rules limits the potential for data snooping bias (Brock et al., 1992). While
this section discusses the general concepts of popular trading rules, Appendix A contains the formal derivation of all rules.

    The first family of rules we test are moving averages. Brock et al. (1992: 1733) state that moving average (MA) rules belong to the
“most popular technical rules” applied in practice. Academically, these rules have gained considerable attention (e.g., Neely et al.,
2014; Han et al., 2016). MA rules generally issue a buy (sell) signal when the actual price, or a relatively recent average price, exceeds
(is below) a longer-term average of the stock price. As recent prices, we use the 1-day, 2-day and 5-day averages, and for longer-term
averages we use the 50-day, 150-day and 200-day averages.

    A second rule that belongs to the most widely used indicators (Brock et al., 1992), is the so-called trading range breakout, also
known as support and resistance levels. This indicator signals minimum and maximum prices, respectively, for which a security has
traded over the past n days. Following Brock et al. (1992) we apply 50, 150 and 200 days for n. A buy signal is issued when the
Bitcoin price exceeds the recent maximum, whereas a sell signal is issued when it is below a recent minimum.

    A third set of rules concerns the moving average convergence divergence (Murphy, 1999). This rule is associated with three
trading signals. One follows from the moving average convergence divergence (MACD) itself, the others from the MACD signal line
and the MACD histogram.

    A fourth rule is the rate of change (ROC) (Taylor and Allen, 1992). This rule relates the current price to the price n days ago. A
common time period used is 10 trading days.

    Fifth, on-balance volume (OBV) is the best-known indicator based on trading volume (Granville, 1963). The OBV indicator
stipulates that volume precedes price changes. The assumption of the OBV indicator is that rising prices reflect positive volume
pressure which in turn can lead to higher prices.

    As a sixth rule, we use the relative strength index (RSI). Wong et al. (2003) suggest that the RSI is the most frequently used
countertrend indicator. The RSI is an oscillator with a level between 0 and 100. According to the RSI, a level higher than 70 normally
indicates that Bitcoin has risen but is now overbought (i.e., one should sell the stock). A level lower than 30 indicates the exact
opposite.

    Seventh, and last, the second countertrend indicator is the Bollinger band method (BB). This rule is related to MA trading rules
because the BB method contains a moving average, around which two bands are plotted (Bollinger, 2001). According to Lento
et al. (2007) the BB (20,2) is the traditional method.

2.2. Bitcoin price, return and trading volume

We use the Bitcoin price history starting from July 17, 2010. At that time, Mt Gox was the best-known exchange for trading

Bitcoin. Due to a hack, there was no trading possible on Mt Gox from June 20, 2011 up to and including June 25, 2011. Hence, we

remove this period from our sample. From April 28, 2013, we use data from Coinmarketcap. In contrast to most securities, Bitcoin is

traded 7 days per week. The last day in our sample is December 31, 2018, giving 3084 daily price observations. In addition to the

Bitcoin price, we collect the risk-free rate of return, for which we use the 3-month US T-bill returns. We compute daily Bitcoin log-
                                                               Bt
returns  using  the     following  equation:  rB,t  =  ln  (  Bt   1  ).  In  addition,  we  gather  the  trading  volume  from  Coinmarketcap.  This  data  is

available only from year-end 2013. Fig. 1 depicts the price evolution of Bitcoin.

2.3. Trading strategies and return evaluation

    We apply the seven families of trading rules in three ways. In the first, we take the trading signal literally. This means that a buy
signal leads to a long-position in Bitcoin, a sell signal to a short-position in Bitcoin and no signal to no position. In the second, we
acknowledge that taking short positions in Bitcoin is in reality not possible across many exchanges. We therefore take a long position
only if a rule issues a buy signal. In all other instances (i.e., sell and hold signals), no position in Bitcoin is held; instead we assume
that the investor invests in an asset that yields the risk-free rate. In the third, based on Brock et al. (1992) and Bessembinder and
Chan (1995), we apply a strategy where an investor has by default a long position in Bitcoin. Following a buy signal, the investor
borrows at the risk-free rate and doubles his investment in Bitcoin. If a sell signal is issued, this investor sells his long position and, as
a consequence, has no position in Bitcoin but is invested in the risk-free asset.

    To evaluate the performance of the seven rules using three strategies, we compute the Sharpe ratio based on daily return and risk

                                                                                                             2


---

D.F. Gerritsen, et al.                 Finance Research Letters 34 (2020) 101263

                        Fig. 1. Bitcoin price evolution from July 2010 to January 2019. Sources: Mt Gox, Coinmarketcap.

data. The Sharpe ratio for rule i is:

Si = Ri                                                                                                                  (1)

           i

where Ri stands for the daily log return as defined in Section 2.2, in excess of the 3-month US treasury-bill rate, σi stands for the
standard deviation of daily returns for a given rule. To assess the relative performance of the trading rules, we compare the Sharpe
ratios of the rules with the Sharpe ratio of a buy-and-hold strategy in Bitcoin as a benchmark. We first compute the difference by
subtracting the buy-and-hold Sharpe ratio from that of a trading rule. Only for readability in tables, we multiply the resulting number
by 100. The comparison of the Sharpe ratios must be based on statistical inference; therefore, we use the bootstrapping method of
Ledoit and Wolf (2008) to measure the statistical significance of the difference between the Sharpe ratios of the daily returns of
Bitcoin for two given portfolios from February 2011 to January 2019. We test whether the Sharpe ratio of the return of portfolio
based on trading rule i is equal to that of the buy-and-hold portfolio as follows:

H0: Ri/ i RB/ B = 0                                                                                                      (2)

where R is the excess return of rule i or Bitcoin B, and σ is the standard deviation of the return of rule i or of buy-and-hold benchmark
B. To test this hypothesis, we calculate a two-sided p-value using M = 1000 bootstrap resamples and then follow the methodology
suggested by Ledoit and Wolf (2008) to generate the resulting bootstrap p-values.2

3. Results

3.1. Full sample results

    The Sharpe ratios of the seven trading rules applied to the daily Bitcoin return from February 20113 to January 2019 are shown in
Table 1, with three results columns associated with the three strategies explained in Section 2.3. The lowest row of the table indicates
the daily Sharpe ratio of the buy-and-hold strategy for the sample period, which equals 0.056 (i.e., an annual Sharpe ratio of 0.056
× 365 = 1.07). The table provides Sharpe ratios for all rules and strategies. The table starts with the results for the well-known
moving average rules. For example, the first row in the “long and short” strategy (i.e., Strategy 1) shows that the Sharpe ratio of the
moving average 1–200 is 0.047, which means a difference from that of the buy-and-hold benchmark of 0.0083 (i.e., 0.83 in basis
points). The associated bootstrapped p-value is 0.65, which means that this difference is not statistically significant. In most appli-
cations, the moving average trading rule does not perform statistically different than the buy-and-hold strategy.

    The trading range breakout rule provides consistently higher Sharpe ratios than the buy-and-hold strategy. On average, across the
various rules and strategies, the Sharpe ratio is around 0.08. For most trading range breakout rules and applied strategies, the
difference in Sharpe ratio with the buy-and-hold benchmark is statistically significant.

    For MACD rules and for the rate-of-change rule, we see significant outperformance only in Strategy 2. Interestingly, the counter-
trend indicators relative strength index and Bollinger bands both not only significantly underperform the buy-and-hold benchmark,
but in some instances even yield negative Sharpe ratios. For on-balance volume, the Sharpe ratios lag those of the buy-and-hold
benchmark, but the differences are not statistically significant.

  2 We use the code available at http://www.iew.uzh.ch/chairs/wolf.html.
  3 Although we used the entire price history as of July 2010, the application of the trading rules starts from February 2011 only. This is because we
relied on price data from prior 200 days to compute the first value of the MA-200.

                                                                                                             3


---

D.F. Gerritsen, et al.                                                                          Finance Research Letters 34 (2020) 101263

Table 1
Sharpe ratios for TA rules given various strategies, full sample period.

Trading rule            Strategy 1: Long, out, and short  Strategy 2: Long or out of Bitcoin    Strategy 3: Double-long, long, or out of
                                                                                                Bitcoin

                        Sharpe ratio Difference from      p-value Sharpe ratio Difference from  p-value Sharpe ratio Difference from    p-value

                                B&H in basis points                       B&H in basis points                B&H in basis points

Moving average

MA1-200                 0.047   −0.83                     0.65 0.066      1.04                  0.31 0.039   −1.66                      0.13
MA1-50                  0.047   −0.89                     0.69 0.079      2.37⁎                 0.08 0.055   0.10                       0.95

MA1-150                 0.045   −1.09                     0.55 0.066      1.06                  0.34 0.040   −1.61                      0.15

MA2-200                 0.051   −0.51                     0.79 0.068      1.22                  0.22 0.041   −1.48                      0.17

MA5-150                 0.053   −0.28                     0.89 0.070      1.40                  0.16 0.043   −1.29                      0.24

Trading range breakout

SUP/RES50               0.081   2.59                      0.21 0.081      2.59                  0.20 0.076   2.04⁎⁎⁎                    0.01
                                3.77⁎                     0.06 0.093      3.77⁎                 0.06 0.074   1.88⁎⁎⁎                    0.01
SUP/RES150              0.093   3.32⁎                     0.07 0.089      3.32⁎                 0.07 0.071   1.55⁎⁎⁎                    0.01

SUP/RES200              0.089

MACD

MACD                    0.060   0.39                      0.85 0.085      2.96⁎⁎                0.02 0.060   0.47                       0.75
                                                          0.78 0.084      2.80⁎⁎                                                        0.81
MACD_SIGNAL 0.062               0.63                      0.93 0.091      3.57⁎⁎⁎               0.02 0.059   0.30                       0.44
                                                          0.98 0.092                                                                    0.43
MACD_HIST               0.058   0.22                                      3.67⁎⁎⁎               0.01 0.067   1.19

Rate of change 0.056            0.06                                                            0.01 0.069   1.32

On balance volume

OBV_MA1-200 0.036               −1.96                     0.36 0.036      −2.00                 0.32 0.051   −0.45                      0.59

OBV_MA1-50              0.008   −4.81⁎                    0.06 0.028      −2.81                 0.18 0.049   −0.68                      0.47

OBV_MA1-150 0.028               −2.74                     0.26 0.032      −2.31                 0.24 0.049   −0.70                      0.41

OBV_MA2-200 0.035               −2.02                     0.41 0.035      −2.03                 0.32 0.051   −0.48                      0.57

   OBV_MA5-150          0.023   −3.22                     0.16 0.029      −2.63                 0.21 0.046   −0.98                      0.26
Rel. strength index     −0.110  −16.61⁎⁎⁎                 0.00 −0.008     −6.33⁎⁎⁎              0.00 −0.022  −7.78⁎⁎⁎                   0.00
Bollinger bands         −0.060  −11.55⁎⁎⁎                 0.00 0.002      −5.34⁎⁎⁎              0.02 0.021   −3.43⁎⁎⁎                   0.00

Buy and hold            0.056

Notes: This table shows the Sharpe ratio on daily basis of all trading rules for three trading strategies applied to daily Bitcoin prices from 2011 to

2018. The column “Difference from B&H in basis points” in each trading rule, provides the difference in basis points between the Sharpe ratio of a

technical analysis rule (TA) and a buy-and-hold strategy (B&H). Following Ledoit and Wolf (2008), we use the bootstrapping approach based on

1000 simulations to test whether the differences in the Sharpe ratios of a technical analysis strategy and a buy-and-hold strategy are zero, the
bootstrapped p-value is reported. ⁎ p < 0.10, ⁎⁎ p < 0.05, ⁎⁎⁎ p < 0.01.

3.2. Subsample results for trading range breakout

    The price development of Bitcoin is characterized by periods of relatively stable markets and boom markets. To better understand
the sensitivity of our results to the choice of the sample period, we identify four periods, (i) 2011–2012, (ii) 2013–2014, (iii)
2015–2016, and (iv) 2017–2018. The first period can be seen as the early years of Bitcoin. It started with an initial boom-and-bust
scenario where the price increased from $0.70 to $29.60 in little more than four months, and subsequently decreased to $2.05 in the
next five months. After these nine months, the price steadily increased to $13.50 at the end of 2012. The second period saw two large
bull markets during the first year, and a continued decline during its second year. The third period was characterized by stable price
increases with no clear peaks or troughs. Lastly, during the fourth period, the price rose to more than $20,000 in the first half, and fell
to around $4000 by the end of the period.

    Table 2 shows the results for the trading range breakout, i.e., the rule which consistently outperforms the buy-and-hold strategy
for the full sample period. Sharpe ratios during the periods 2011–2012, 2013–2014 and 2017–2018 are higher than those of the buy-
and-hold benchmark. In the latter two periods, we find that some variations of this rule deliver statistically significant out-
performance. The period 2015–2016, however, yields Sharpe ratios which are generally lower than those of the buy-and-hold
benchmark. The difference from the other three periods is that this was a relatively stable period, not characterized by one or more
clear bull or bear markets. Therefore, the added value of the trading rule depends on the market conditions. In strongly trending
markets, the trading range breakout rule seems to deliver outperformance. This concords with the adaptive market hypothesis of
Lo (2004), which indicates that the performance of trading strategies is environment-dependent. But it is not unusual for Bitcoin to
perform less erratically for an extended period of time. In such a period, trading range breakout rules lag a simple buy-and-hold
strategy. This underperformance is, however, not statistically significant. For reasons of completeness, we present the performance
for all rules during the subsample periods in Tables B1–B4 in Appendix B. Most rules do not exhibit structural outperformance during
the sub-periods.4

4 The rate of change significantly outperforms in the first two sub-periods, but loses its outperformance during the last two periods.
                                                                                                          4


---

D.F. Gerritsen, et al.                                                                                     Finance Research Letters 34 (2020) 101263

Table 2
Sharpe ratios for trading range breakout for subsample periods.

Trading range           Strategy 1: Long, out, and short  Strategy 2: Long or out of Bitcoin    Strategy 3: Double-long, long, or out of
breakout                                                                                        Bitcoin

                        Sharpe ratio Difference from      p-value Sharpe ratio Difference from  p-value Sharpe ratio Difference from  p-value

                                   B&H in basis points                  B&H in basis points                B&H in basis points

2011–2012

SUP/RES50               0.09       2.41                   0.61 0.09     2.41                    0.59 0.09  2.65                       0.13

SUP/RES150 0.10                    3.20                   0.44 0.10     3.20                    0.44 0.09  1.89                       0.25

SUP/RES200 0.09                    2.58                   0.47 0.09     2.58                    0.46 0.08  1.19                       0.17

Buy-and-hold 0.07

2013–2014

SUP/RES50               0.11       5.45                   0.15 0.11     5.45                    0.13 0.08  2.62                       0.16
                                   7.52⁎⁎                 0.03 0.13     7.52⁎                   0.05 0.09  3.06⁎                      0.08
SUP/RES150 0.13                    6.30⁎                  0.09 0.12     6.30⁎                   0.09 0.08                             0.15
                                                                                                           2.55
SUP/RES200 0.12

Buy-and-hold 0.06

2015–2016

SUP/RES50               0.05       −1.96                  0.56 0.05     −1.96                   0.60 0.07  0.01                       0.99

SUP/RES150 0.02                    −4.31                  0.25 0.02     −4.31                   0.23 0.06  −0.65                      0.53

SUP/RES200 0.03                    −3.51                  0.35 0.03     −3.51                   0.35 0.06  −0.32                      0.73

Buy-and-hold 0.07

2017–2018

SUP/RES50               0.07       2.76                   0.50 0.07     2.76                    0.54 0.06  2.07                       0.12
                                                                                                0.17 0.07  2.33⁎⁎                     0.04
SUP/RES150 0.10                    5.57                   0.17 0.10     5.54                    0.19 0.03  2.33⁎⁎                     0.04

SUP/RES200 0.10                    5.54                   0.17 0.10     5.54

Buy-and-hold 0.04

Notes: This table depicts the Sharpe ratio on a daily basis of the trading range breakout rules for four subsample periods. The column “Difference

from B&H in basis points” in each trading rule, provides the difference in basis points between the Sharpe ratio of a technical analysis rule (TA) and a

buy-and-hold strategy (B&H). Following Ledoit and Wolf (2008), we use the bootstrapping approach based on 1000 simulations to test whether the
differences in the Sharpe ratios of a technical analysis strategy and a buy-and-hold strategy are zero, the bootstrapped p-value is reported. ⁎ p <
0.10, ⁎⁎ p < 0.05, ⁎⁎⁎ p < 0.01.

4. Conclusion

    In this paper, we show that the profitability of specific technical trading rules, such as the trading range breakout rule, can
consistently exceed that of a buy-and-hold strategy for the full sample period and during strongly trending markets. Practically, we
have shown that the use of specific technical trading rules allows generating excess returns, which is useful to Bitcoin traders and
investors in making trading and investment decisions. The findings can be seen as new evidence against the market efficiency of
Bitcoin (Tiwari et al., 2018), extending prior studies that consider the predictability of Bitcoin prices based on attention
(Dastgir et al., 2019), trading volume (Blacilar et al., 2017), other cryptocurrencies (Bouri et al., 2019; Ji et al., 2019), geopolitical
risks (Aysan et al., 2019), economic uncertainty (Demir et al., 2018), stock market uncertainty (Bouri et al., 2017), and energy/
commodity prices (Hayes, 2017; Bouri et al., 2018). Future research should focus on other leading cryptocurrencies and consider the
profitability of the trading range breakout rule after the inclusion of transaction costs (Hudson et al., 1996).

Appendix A. Definition of technical analysis trading rules

A.1. Moving average

    The moving average rule starts with the computation of an average price during a past period. More formally constructed, for
Bitcoin (B) the outcome of an MA at time t based on n observations can be defined as:

MA (B)t,n =             1     t    n+1 B
                        n     j=t

= (Bt + Bt 1+…+Bt n+2 + Bt n+1)/n

    In this equation, MA(B)t,n is the simple n-day moving average for Bitcoin at day t, and Bt is the closing price for Bitcoin at day t.
Hence, the calculated value of MA(B) at time t is positioned at the same spot on the time axis as the last observation of Bt used in the
definition. An infinite number of combinations of long-term (MAL) and short-term averages (MAS) can be made. However, to mitigate
potential biases introduced by data snooping, we follow Brock et al. (1992: 1735), restraining ourselves to the “most popular ones”:
1–50, 1–150, 5–150, 1–200 and 2–200 where the first number is the MAS and the second number the MAL. Since Bitcoin is traded on
all calendar days of the year, these rules concern returns for a period of around one-week, half a quarter, one-and-a-half quarters, and
a half a year. For the purpose of defining trading rules, let k be the number of periods for MAS and l the number of periods for MAL.
The trading rules can be summarized as: “Buy” if MAS(B)t,k crosses MAL(B)t,l from below and as long as MAS(B)t,k > MAL(B)t,l. A
“Sell” signal is issued if MAL(B)t,l crosses MAS(B)t,k from above and as long as MAS(B)t,k < MAL(B)t,l.

                                                                     5


---

D.F. Gerritsen, et al.                                                                                                     Finance Research Letters 34 (2020) 101263

A.2. Trading range breakout

    This rule distinguishes both a support and a resistance level of the Bitcoin price. These levels are defined as follows:
         SUPPORT (B)t = MIN (Bt 1, Bt 2, …, Bt n 1)

         RESISTANCE (B)t = MAX (Bt 1, Bt 2, …, Bt n 1).

    Following Brock et al. (1992), we apply 50, 150 and 200 days for n. As an example, the 50-day resistance level for stock i on day t
is the maximum stock price during the previous 50 trading days. According to this rule, investors usually sell at the local maximum
price. If on the other hand the stock price increases above this so-called resistance level, this rule issues a bullish signal. The reverse
holds for the support level. The trading rule can thus be defined as “Buy” if Bt > RESISTANCE(B)t and “Sell” if Bt < SUPPORT(B)t.

A.3. Moving average convergence divergence

The MACD is based on two exponential moving averages (EMA) and is defined as the difference between two EMAs. According to

Murphy (1999), the 12-day EMA and the 26-day EMA are the most frequently used. The EMA is a variant of the simple MA, but this
                                                                                                                           2
rule  gives  a  higher  weighting  to  the  most    recent  closing  price.  This    weighting  factor  is  defined  as  n+   1  where  n  is  the  EMA-period.  The

MA(B)t,n is generally used as a value for the first-day EMA-period. The following equations first define the exponential moving

average where n is 12 for the 12-day EMA, and n is 26 for the 26-day EMA. Then the MACD rule which is based on two exponential

moving averages is defined.

      EMA (B)t,n = [Bt  EMA (B)t            1,n] ×    2     + EMA (B)t  1,n
                                                    n+1

      MACD (B)t = EMA (B)t,12 EMA (B)t,26

    The following trading rule is followed: “Buy” as long as MACD(B)t > 0 and “Sell” as long as MACD(B)t < 0.
    The MACD signal line is a method related to the MACD. In this case, a 9-day EMA of the MACD is constructed. This is the so-called
signal line:

      MACDSIGNAL (B)t = [MACD (B)t                  EMA (MACD (B))t          1,9] ×    2  + EMA (MACD (B))t          1, 9
                                                                                     n+1

    MA(MACD(B))t − 1, 9 is used as a starting value. The following trading rule can be defined: “Buy” if MACDSIGNAL(B)t > 0 and
“Sell” if MACDSIGNAL(B)t < 0.

    Another method related to the MACD is the MACD histogram, which represents the difference between the MACD and the signal
line:

         MACDHISTOGRAM (B)t = MACD (B)t MACDSIGNAL (B)t.

    Positive histogram values indicate an uptrend, and negative values indicate a downtrend. In other words: “Buy” as long as
MACDHISTOGRAM(B)t > 0 and “Sell” as long as MACDHISTOGRAM(B)t < 0.

A.4. Rate of change

    The rate of change typically compares the price to the price n days ago. For n, we use 10 trading days.
         ROC (B)t = Bt Bt 9

    A price increase corresponds to a positive momentum, and a negative value of ROC indicates negative momentum. The resulting
trading rule is defined as follows: “Buy” as long as ROC(B)t > 0 and “Sell” as long as ROC(B)t < 0.

A.5. On balance volume

    The on balance volume (OBV) indicator starts at 0 and adds trading volume (V) of positive trading days (i.e., days during which
the stock closed up) and deducts V negative trading days (i.e., days during which the stock closed down):

      OBV (B)t = OBV (B)t 1 +          V if Bt > Bt 1
                                       0 if Bt = Bt 1

                                        V if Bt < Bt 1

    Usually MA rules are applied to the OBV. Again, we refer to the short-term moving average as MAS and the long-term moving
average as MAL. We consider the following MA rules: MA 1–50, MA 1–150, MA 5–150, MA 1–200 and MA 2–200. This brings us to
the following trading signals: “Buy” if MAS(OBVi)t,k crosses MAL(OBVi)t,l upwards and as long as MAS(OBVi)t,k > MAL(OBVi)t,l; “Sell”
when MAS(OBVi)t,k crosses MAL(OBVi)t,l downwards and as long as MAS(OBVi)t,k < MAL(OBVi)t,l.

                                                                             6


---

D.F. Gerritsen, et al.                                                                                           Finance Research Letters 34 (2020) 101263

A.6. Relative strength index

    The RSI uses closing prices and is the ratio of up-closes, Ui,t, to down-closes, Di,t, over the time period selected. The length of this
period is usually 14 days. The up-closes and down-closes are defined such that:

Ui,t Bt                 Bt 1 if Bt > Bt 1  and Di,t  Bt 1 Bt if Bt 1 > Bt
                        0 otherwise                        0 otherwise

The next step is to define the average level of the up- and down-closes:

U¯ (B)t    =            1      t   U (B)t
                        14     13
                            t

D¯ (B)t    =            1      t   D (B)t
                        14     13
                            t

The relative strength for Bitcoin at time t is calculated as follows:

RS (B)t =               U¯     (B)t  .
                        D¯     (B)t

The RSI for Bitcoin at time t is defined as: RSI (B)t = 100                1  +  100  (B)t  .
                                                                                 RS

Hence, the RSI method can be interpreted as a countertrend indicator. The trading rules can be summarized as: “Buy” as long as

RSI(B)t < 30 and “Sell” as long as RSI(B)t > 70.

A.7. Bollinger bands

    The Bollinger bands (BB) method contains a moving average, around which two bands are plotted (Bollinger, 2001). The BB
(20,2) is the traditional method (Lento, 2007).This refers to a 20-day moving average where the distance between the MA and the
bands is twice the standard deviation of the Bitcoin price measured over the most recent 20-day period, σB,20. At time t the upper
band for Bitcoin can thus be defined as:

         BBUPPER (B)t = MA (B)t,20 + 2 B,20.

    The lower band can be defined as:

         BBLOWER (B)t = MA (B)t,20 2 B,20.

    When the actual stock price exceeds one of those bands, it signals, according to the BB rule, that the stock price will return to the
moving average. The BB method can thus be considered as a countertrend indicator. The trading rules can be specified as follows:
“Buy” as long as B< BBLOWER(B)t and “Sell” as longs as B > BBUPPERt.

Appendix B. Sharpe ratios for TA rules for various strategies and subsample periods

Table B1
Sharpe ratios for TA rules given various strategies, February 2011–December 2012.

Technical analysis Rule 1: Long, out, and short                 Rule 2: Long or out of Bitcoin        Rule 3: Double-long, long, or out of Bitcoin

                            Sharpe ratio Difference from        p-value Sharpe ratio Difference from  p-value Sharpe ratio Difference from  p-value

                                           B&H in basis points                   B&H in basis points             B&H in basis points

Moving average

MA1-200                     0.04           −3.02                0.45 0.07        0.33                 0.90 0.03  −3.34                      0.19
                                           1.51                 0.73 0.11        4.33                 0.15 0.07  0.84                       0.82
MA1-50                      0.08           −2.44                0.55 0.07        0.60                 0.80 0.04  −3.12                      0.21
                                           −2.72                0.52 0.07        0.54                 0.80 0.03  −3.14                      0.18
MA1-150                     0.04           0.36                 0.92 0.09        1.88                 0.42 0.05  −1.94                      0.42

MA2-200                     0.04           2.41                 0.61 0.09        2.41                 0.59 0.09
                                           3.20                 0.44 0.10        3.20                 0.44 0.09
MA5-150                     0..07          2.58                 0.47 0.09        2.58                 0.46 0.08

Trading range breakout                     1.68                 0.72 0.11        4.35                 0.13 0.08
                                           2.25                 0.62 0.11        4.53                 0.10 0.08
SUP/RES50                   0.09           −0.51                0.92 0.10        2.96                 0.22 0.06  2.65                       0.13

SUP/RES150                  0.10                                                                                 1.89                       0.25

SUP/RES200                  0.09                                                                                 1.19                       0.17

MACD

MACD                        0.08                                                                                 0.88                       0.80
                                                                                                                 1.04                       0.75
MACD_SIGNAL 0.09                                                                                                 −0.49                      0.86

MACD_HIST                   0.06

                                                                                                                       (continued on next page)

                                                                           7


---

D.F. Gerritsen, et al.                                                                                 Finance Research Letters 34 (2020) 101263

Table B1 (continued)

Technical analysis Rule 1: Long, out, and short          Rule 2: Long or out of Bitcoin        Rule 3: Double-long, long, or out of Bitcoin

                        Sharpe ratio Difference from  p-value Sharpe ratio Difference from  p-value Sharpe ratio Difference from  p-value

                               B&H in basis points                   B&H in basis points                B&H in basis points

   Rate of change       0.09   2.58                   0.63 0.12      5.33⁎                  0.08 0.08   1.84                      0.63
On balance volume
                        –      –                      –  –           –                      –  –        –                         –
   OBV_MA1-200          –      –                                     –                                  –                         –
   OBV_MA1-50           –      –                      –  –           –                      –  –        –                         –
   OBV_MA1-150          –      –                                     –                                  –                         –
   OBV_MA2-200          –      –                      –  –           –                      –  –        –                         –
   OBV_MA5-150          −0.14  −20.11                                −7.13                              −9.71⁎⁎⁎                  0.00
Rel. strength index     −0.10  −9.69                  –  –           −4.05                  –  –        −2.14                     0.25
Bollinger bands         0.07
Buy and hold                                          –  –                                  –  –

                                                      0.00 −0.02                            0.17 −0.04

                                                      0.10 −0.01                            0.42 0.00

                                                         0.07                                  0.07

This table shows the Sharpe ratio on daily basis of all trading rules for three trading strategies applied to daily Bitcoin prices from 2011 to 2018. The

column “Difference from B&H in basis points” in each trading rule, provides the difference in basis points between the Sharpe ratio of a technical

analysis rule (TA) and a buy-and-hold strategy (B&H). Volume data was not available for this time period. Following Ledoit and Wolf (2008), we use

the bootstrapping approach based on 1000 simulations to test whether the differences in the Sharpe ratios of a technical analysis strategy and a buy-
and-hold strategy are zero, the bootstrapped p-value is reported. ⁎ p < 0.10, ⁎⁎ p < 0.05, ⁎⁎⁎ p < 0.01.

Table B2
Sharpe ratios for TA rules given various strategies, January 2013–December 2014.

Technical analysis Rule 1: Long, out, and short          Rule 2: Long or out of Bitcoin        Rule 3: Double-long, long, or out of Bitcoin

                        Sharpe ratio Difference from  p-value Sharpe ratio Difference from  p-value Sharpe ratio Difference from  p-value

                               B&H in basis points                   B&H in basis points                B&H in basis points

Moving average

MA1-200                 0.07   1.59                   0.61 0.08      2.06                   0.27 0.05   −0.93                     0.63

MA1-50                  0.04   −1.77                  0.68 0.07      1.82                   0.47 0.05   −0.96                     0.73

MA1-150                 0..04  −1.22                  0.76 0.07      0.89                   0.66 0.04   −1.96                     0.32

MA2-200                 0.07   1.68                   0.63 0.08      2.11                   0.23 0.05   −0.88                     0.64

MA5-150                 0.05   −0.63                  0.88 0.07      1.21                   0.54 0.04   −1.66                     0.43

Trading range breakout

SUP/RES50               0.11   5.45                   0.15 0.11      5.45                   0.13 0.08   2.62                      0.16
SUP/RES150              0.13   7.52⁎⁎                 0.03 0.13      7.52⁎                  0.05 0.09   3.06⁎                     0.08
SUP/RES200              0.12   6.30⁎                  0.09 0.12      6.30⁎                  0.09 0.08                             0.15
                                                                                                        2.55

MACD

MACD                    0.08   2.26                   0.58 0.09      3.75                   0.11 0.07   0.90                      0.72

MACD_SIGNAL 0.08               1.93                   0.61 0.09      3.10                   0.15 0.06   0.26                      0.92

MACD_HIST               0.06   0.67                   0.88 0.10      4.52                   0.10 0.08   2.01                      0.51

Rate of change 0.06            0.50                   0.92 0.10      4.54⁎                  0.09 0.08   1.99                      0.53

On balance volume

OBV_MA1-200 –                  –                      –  –           –                      –  –        –                         –

OBV_MA1-50              –      –                      –  –           –                      –  –        –                         –

OBV_MA1-150 –                  –                      –  –           –                      –  –        –                         –

OBV_MA2-200 –                  –                      –  –           –                      –  –        –                         –

OBV_MA5-150 –                  –                      –  –           –                      –  –        –                         –

Rel. strength index −0.14      −13.63⁎                0.04 −0.01     −4.59                  0.36 −0.04  −4.16                     0.12

Bollinger bands         −0.04  −8.53                  0.19 0.02      −4.95                  0.37 0.03   −0.34                     0.83

Buy and hold            0.06                             0.06                                  0.06

This table shows the Sharpe ratio on daily basis of all trading rules for three trading strategies applied to daily Bitcoin prices from 2011 to 2018. The

column “Difference from B&H in basis points” in each trading rule, provides the difference in basis points between the Sharpe ratio of a technical

analysis rule (TA) and a buy-and-hold strategy (B&H). Volume data was not available for this time period. Following Ledoit and Wolf (2008), we use

the bootstrapping approach based on 1000 simulations to test whether the differences in the Sharpe ratios of a technical analysis strategy and a buy-
and-hold strategy are zero, the bootstrapped p-value is reported. ⁎ p < 0.10, ⁎⁎ p < 0.05, ⁎⁎⁎ p < 0.01.

                                                                  8


---

D.F. Gerritsen, et al.                                                                                      Finance Research Letters 34 (2020) 101263

Table B3
Sharpe ratios for TA rules given various strategies, January 2015–December 2016.

Technical analysis Rule 1: Long, out, and short       Rule 2: Long or out of Bitcoin             Rule 3: Double-long, long, or out of Bitcoin

                        Sharpe ratio Difference from  p-value Sharpe ratio Difference from       p-value Sharpe ratio Difference from  p-value

                               B&H in basis points                          B&H in basis points             B&H in basis points

Moving average

MA1-200                 0.03   −4.23                  0.26 0.06             −0.91                0.63 0.04  −2.32                      0.27
                               −3.81                  0.37 0.06             −0.31                0.91 0.05  −1.62                      0.51
MA1-50                  0.03   −3.89                  0.33 0.06             −0.74                0.73 0.05  −2.16                      0.30
                               −3.95                  0.30 0.06             −0.75                0.73 0.05  −2.16                      0.28
MA1-150                 0.03   −3.21                  0.39 0.06             −0.39                0.83 0.05  −1.82                      0.35

MA2-200                 0.03   −1.96                  0.56 0.05             −1.96
                               −4.31                  0.25 0.02             −4.31
MA5-150                 0.04   −3.51                  0.35 0.03             −3.51

Trading range breakout         −2.95                  0.48 0.07             0.34
                               −3.69                  0.39 0.07             −0.12
SUP/RES50               0.05   −0.77                  0.87 0.09             2.40                 0.60 0.07  0.01                       0.99
                               −5.21                  0.20 0.06             −0.63                0.23 0.06  −0.65                      0.53
SUP/RES150              0.02                                                                     0.35 0.06  −0.32                      0.73
                               1.93                   0.40 0.05             1.39
SUP/RES200              0.03   −7.09                  0.10 0.07             −2.32
                               1.62                   0.45 0.05             1.25
MACD                           1.85                   0.39 0.05             1.34
                               0.78                   0.75 0.04             0.87
MACD                    0.0.4  −12.99⁎⁎               0.03 0.02             −3.33                0.88 0.06  −0.95                      0.67
                               −9.64⁎                 0.05 0.02             −5.26                0.96 0.05  −1.41                      0.55
MACD_SIGNAL 0.03                                                                                 0.31 0.08  1.24                       0.63
                                                                   0.07                          0.79 0.05  −1.81                      0.49
MACD_HIST               0.06

Rate of change 0.02

On balance volume

OBV_MA1-200 0.02                                                                                 0.20 0.03  −0.87                      0.43

OBV_MA1-50              0.03                                                                     0.31 0.05  −4.21                      0.08

OBV_MA1-150 0.01                                                                                 0.29 0.03  −1.00                      0.37

OBV_MA2-200 0.02                                                                                 0.22 0.03  −0.91                      0.41

OBV_MA5-150 0.01                                                                                 0.49 0.03  −1.37                      0.25
                                                                                                 0.43 0.03  −5.37⁎⁎                    0.03
Rel. strength index −0.07                                                                        0.19 0.06  −2.97⁎⁎                    0.03

Bollinger bands         −0.02

Buy and hold            0.07                                                                     0.07

This table shows the Sharpe ratio on daily basis of all trading rules for three trading strategies applied to daily Bitcoin prices from 2011 to 2018. The

column “Difference from B&H in basis points” in each trading rule, provides the difference in basis points between the Sharpe ratio of a technical

analysis rule (TA) and a buy-and-hold strategy (B&H). Following Ledoit and Wolf (2008), we use the bootstrapping approach based on 1000

simulations to test whether the differences in the Sharpe ratios of a technical analysis strategy and a buy-and-hold strategy are zero, the boot-
strapped p-value is reported. ⁎ p < 0.10, ⁎⁎ p < 0.05, ⁎⁎⁎ p < 0.01.

Table B4
Sharpe ratios for TA rules given different strategies, January 2017–December 2018.

Technical analysis Rule 1: Long, out, and short       Rule 2: Long or out of Bitcoin             Rule 3: Double-long, long, or out of Bitcoin

                        Sharpe ratio Difference from  p-value Sharpe ratio Difference from       p-value Sharpe ratio Difference from  p-value

                               B&H in basis points                          B&H in basis points             B&H in basis points

Moving average

MA1-200                 0.06   1.51                   0.68 0.06             2.31                 0.24 0.04  0.27                       0.90
                               −1.40                  0.79 0.07             2.39                 0.40 0.05
MA1-50                  0.03   2.88                   0.46 0.08             3.54                 0.10 0.06  0.71                       0.83
                               2.25                   0.54 0.07             2.68                 0.19 0.05
MA1-150                 0.07   1.16                   0.77 0.07             2.48                 0.25 0.05  1.60                       0.48

MA2-200                 0.06   2.76                   0.50 0.07             2.76                 0.54 0.06  0.63                       0.76
                               5.57                   0.17 0.10             5.54                 0.17 0.07
MA5-150                 0.05   5.54                   0.17 0.10             5.54                 0.19 0.07  0.53                       0.81

Trading range breakout         −1.57                  0.75 0.06             2.07                 0.45 0.05
                               −0.43                  0.93 0.07             2.33                 0.37 0.05
SUP/RES50               0.07   1.41                   0.81 0.09             5.09⁎                0.09 0.08  2.07                       0.12
                               −0.73                  0.89 0.08             3.63                 0.25 0.06  2.33⁎⁎                     0.04
SUP/RES150              0.10                                                                                2.33⁎⁎                     0.04
                               1.96                   0.39 0.06             1.41                 0.24 0.03
SUP/RES200              0.10   −7.09                  0.13 0.02             −2.32                0.34 0.00
                               1.65                   0.49 0.06             1.28                 0.26 0.03
MACD

MACD                    0.03                                                                                0.34                       0.90

MACD_SIGNAL 0.04                                                                                            0.51                       0.84

MACD_HIST               0.06                                                                                3.66                       0.22

Rate of change 0.03                                                                                         2.18                       0.51

On balance volume

OBV_MA1-200 0.06                                                                                            −0.85                      0.46
                                                                                                            −4.21⁎                     0.07
OBV_MA1-50              −0.03

OBV_MA1-150 0.06                                                                                            −0.97                      0.40

                                                                                                                  (continued on next page)

                                                                         9


---

D.F. Gerritsen, et al.                                                                            Finance Research Letters 34 (2020) 101263

Table B4 (continued)

Technical analysis Rule 1: Long, out, and short       Rule 2: Long or out of Bitcoin              Rule 3: Double-long, long, or out of Bitcoin

                        Sharpe ratio Difference from  p-value Sharpe ratio Difference from        p-value Sharpe ratio Difference from    p-value

                               B&H in basis points                           B&H in basis points                     B&H in basis points

   OBV_MA2-200          0.06   1.88                   0.41 0.06              1.37                 0.21 0.03          −0.89                0.45
   OBV_MA5-150          0.05                          0.74 0.05              0.89                 0.44 0.03                               0.26
Rel. strength index     −0.09  0.81                   0.04 0.01              −3.33                0.43 −0.01         −1.35                0.04
Bollinger bands         −0.05  −12.98⁎⁎               0.04 −0.01             −5.25                0.21 0.01          −5.37⁎⁎              0.04
Buy and hold            0.04   −9.63⁎⁎                                                                               −2.97⁎⁎
                                                                   0.04                                        0.04

This table shows the Sharpe ratio on daily basis of all trading rules for three trading strategies applied to daily Bitcoin prices from 2011 to 2018. The

column “Difference from B&H in basis points” in each trading rule, provides the difference in basis points between the Sharpe ratio of a technical

analysis rule (TA) and a buy-and-hold strategy (B&H). Following Ledoit and Wolf (2008), we use the bootstrapping approach based on 1000

simulations to test whether the differences in the Sharpe ratios of a technical analysis strategy and a buy-and-hold strategy are zero, the boot-
strapped p-value is reported. ⁎ p < 0.10, ⁎⁎ p < 0.05, ⁎⁎⁎ p < 0.01.

References

Aysan, A.F., Demir, E., Gozgor, G., Lau, C.K.M., 2019. Effects of the geopolitical risks on Bitcoin returns and volatility. Res. Int. Business Finance 47, 511–518.
Bessembinder, H., Chan, K., 1995. The profitability of technical trading rules in the Asian stock markets. Pacific-Basin Finance J. 3 (2–3), 257–284.
Bollinger, J., 2001. Bollinger on Bollinger Bands. McGraw Hill.
Brock, W., Lakonishok, J., LeBaron, B., 1992. Simple technical trading rules and the stochastic properties of stock returns. J. Finance 47 (5), 1731–1764.
Balcilar, M., Bouri, E., Gupta, R., Roubaud, D., 2017. Can volume predict Bitcoin returns and volatility? A quantiles-based approach. Econ. Model. 64, 74–81.
Bouri, E., Gupta, R., Tiwari, A.K., Roubaud, D., 2017. Does Bitcoin hedge global uncertainty? Evidence from wavelet-based quantile-in-quantile regressions. Finance

     Res. Lett. 23, 87–95.
Bouri, E., Gupta, R., Lahiani, A., Shahbaz, M., 2018. Testing for asymmetric nonlinear short-and long-run relationships between bitcoin, aggregate commodity and gold

     prices. Resources Policy 57, 224–235.
Bouri, E., Shahzad, S.J.H., Roubaud, D., 2019. Co-explosivity in the cryptocurrency market. Finance Res. Lett. 29, 178–183.
Dastgir, S., Demir, E., Downing, G., Gozgor, G., Lau, C.K.M., 2019. The causal relationship between Bitcoin attention and Bitcoin returns: evidence from the copula-

     based Granger causality test. Finance Res. Lett. 28, 160–164.
Demir, E., Gozgor, G., Lau, C.K.M., Vigne, S.A., 2018. Does economic policy uncertainty predict the Bitcoin returns? An empirical investigation. Finance Res. Lett. 26,

     145–149.
Dyhrberg, A.H., 2016. Bitcoin, gold and the dollar—a Garch volatility analysis. Finance Res. Lett. 16, 85–92.
Gerritsen, D.F., 2016. Are chartists artists? the determinants and profitability of recommendations based on technical analysis. Int. Rev. Financial Anal. 47, 179–196.
Granville, J.E., 1963. Granville's New Strategy of Daily Stock Market Timing For Maximum Profit. Prentice-Hall.
Han, Y., Zhou, G., Zhu, Y., 2016. A trend factor: any economic gains from using information over investment horizons? J. Financ. Econ. 122, 352–375.
Hayes, A.S., 2017. Cryptocurrency value formation: an empirical study leading to a cost of production model for valuing bitcoin. Telematics Inform. 34 (7),

     1308–1321.
Hudson, R., Dempsey, M., Keasey, K., 1996. A note on the weak form efficiency of capital markets: the application of simple technical trading rules to UK stock prices-

     1935 to 1994. J. Bank. Financ. 20 (6), 1121–1132.
Ji, Q., Bouri, E., Lau, C.K.M., Roubaud, D., 2019. Dynamic connectedness and integration in cryptocurrency markets. Int. Rev. Financial Anal. 63, 257–272.
Kristoufek, L., 2015. What are the main drivers of the Bitcoin price? Evidence from wavelet coherence analysis. PLoS ONE 10 (4), e0123923.
Ledoit, O., Wolf, M., 2008. Robust performance hypothesis testing with the Sharpe ratio. J. Empir. Finance 15 (5), 850–859.
Lento, C., Gradojevic, N., Wright, C.S., 2007. Investment information content in Bollinger Bands? Appl. Financial Econ. Lett. 3 (4), 263–267.
Lo, A., 2004. The adaptive markets hypothesis: market efficiency from an evolutionary perspective. J. Portfolio Manage. 30 (5), 15–29.
Neely, C.J., Rapach, D.E., Tu, J., Zhou, G., 2014. Forecasting the equity risk premium: the role of technical indicators. Manage. Sci. 60 (7), 1772–1791.
Taylor, M.P., Allen, H., 1992. The use of technical analysis in the foreign exchange market. J. Int. Money Finance 11 (3), 304–314.
Tiwari, A.K., Jana, R.K., Das, D., Roubaud, D., 2018. Informational efficiency of Bitcoin—an extension. Econ. Lett. 163, 106–109.
Wong, W., Manzur, M., Chew, B., 2003. How rewarding is technical analysis? Evidence from Singapore stock market. Appl. Financial Econ. 13 (7), 543–551.

                                                                         10


---


