# Technical Trading And Cryptocurrencies

Source PDF: technical trading-and-cryptocurrencies.pdf

---

Annals of Operations Research (2021) 297:191–220
https://doi.org/10.1007/s10479-019-03357-1

S.I.: NETWORKS AND RISK MANAGEMENT

Technical trading and cryptocurrencies

Robert Hudson1 · Andrew Urquhart2

Published online: 30 August 2019
© The Author(s) 2019

Abstract
This paper carries out a comprehensive examination of technical trading rules in cryptocur-
rency markets, using data from two Bitcoin markets and three other popular cryptocurrencies.
We employ almost 15,000 technical trading rules from the main ﬁve classes of technical trad-
ing rules and ﬁnd signiﬁcant predictability and proﬁtability for each class of technical trading
rule in each cryptocurrency. We ﬁnd that the breakeven transaction costs are substantially
higher than those typically found in cryptocurrency markets. To safeguard against data-
snooping, we implement a number of multiple hypothesis procedures which conﬁrms our
ﬁndings that technical trading rules do offer signiﬁcant predictive power and proﬁtability to
investors. We also show that the technical trading rules offer substantially higher risk-adjusted
returns than the simple buy-and-hold strategy, showing protection against lengthy and severe
drawdowns associated with cryptocurrency markets. However there is no predictability for
Bitcoin in the out-of-sample period, although predictability remains in other cryptocurrency
markets.

Keywords Technical analysis · Cryptocurrencies · Bitcoin · Data-snooping · Market
efﬁciency

1 Introduction

Cryptocurrencies are a new type of ﬁnancial instrument that have received a great amount of
interest both from the media and investors in the recent past. The ﬁrst cryptocurrency created
was Bitcoin, proposed by Nakamoto (2008), as a peer-to-peer electronic cash system which
allows online payments to be sent directly from one party to another without going through
a ﬁnancial institutions. Therefore unlike most other ﬁnancial instruments, Bitcoin has no
association with any authority and has no physical representation. The value of Bitcoin is not
based on any tangible asset or any country’s economy and instead is based upon the security
of an algorithm which traces all transactions. The potential use of Bitcoin as a medium of

B Andrew Urquhart

     a.j.urquhart@icmacentre.ac.uk

     Robert Hudson
     robert.hudson@hull.ac.uk

1 Hull University Business School, University of Hull, Hull, UK
2 ICMA Centre, Henley Business School, University of Reading, Reading, UK

                                                                           123


---

192  Annals of Operations Research (2021) 297:191–220

exchange is attractive due to its low transaction costs, its peer-to-peer, global and government-
free design. However users may be concerned by the lack of conﬁdence in the system as well
as the lack of acceptability of Bitcoin to make transactions. As discussed above, Bitcoin was
conceived as a new type of currency rather than an investment asset. However, Fig. 1 shows
the price of Bitcoin and other cryptocurrencies has increased substantially since 2010 with
Baur et al. (2018) showing that Bitcoin accounts are mainly used as a speculative investment
rather than an alternative currency or medium of exchange, which is supported by Corbet
et al. (2018). The investment suitability of Bitcoin has been hotly debated. Charlie Munger,
the billionaire investor and partner of Warren Buffet, for example, stated “I regard the bitcoin
craze as totally asinine” (Financial Times, 2018).1 Much of the criticism of Bitcoin has been
on the grounds of its lack of intrinsic value. Nonetheless, the academic literature examining
the price dynamics of Bitcoin and other cryptocurrencies is growing, with a number of papers
studying bubbles in cryptocurrency markets (Cheah and Fry 2015; Fry and Cheah 2016;
Corbet et al. 2018), the market efﬁciency of Bitcoin markets (Urquhart 2016; Nadarajah and
Chu 2017; Bariviera 2017; Tiwari et al. 2018), the hedging properties of Bitcoin (Brière et al.
2015; Dyhrberg 2016a, b; Bouri et al. 2017; Urquhart and Zhang 2019), the price discovery
within Bitcoin exchanges (Brandvold et al. 2015; Brauneis and Mestel 2018) as well as price
clustering Urquhart (2017). Nevertheless, the ﬁnance literature concerning Bitcoin and other
cryptocurrencies is limited since they are fairly new ﬁnancial assets.

   An area that has received increasing attention in the cryptocurrency literature is the ben-
eﬁts of investing in cryptocurrencies. Kajtazi and Moro (2019) explore the effects of adding
Bitcoin to an optimal portfolio (naïve, long-only, semi-constrained with and without Bitcoin
shorting) by relying on the mean-CVaR approach for US, European and Chinese portfolio
assets. They show that Bitcoin improves the returns of the portfolio, mostly from increased
returns rather than lower volatility, and that Bitcoin has a role in portfolio diversiﬁcation.
Recently, Platanakis and Urquhart (2019) examine the out-of-sample beneﬁt of including
Bitcoin in eight popular asset allocation strategies in portfolios of stocks and bonds. They
ﬁnd that the inclusion of Bitcoin generates substantially higher risk-adjusted returns, where
the results are robust to a different structure of estimation windows, the incorporation of
transaction costs, the inclusion of a commodity portfolio, an alternative index for Bitcoin as
well as two additional portfolio optimization techniques including higher moments with (and
without) variance-based constraints.In respect of the optimisation of cryptocurrency portfo-
lios Platanakis et al. (2018) examine the performance of nave (1/N) and optimal (Markowitz)
diversiﬁcation in a portfolio of four popular cryptocurrencies. They show there is very little
to differentiate between nave diversiﬁcation and optimal diversiﬁcation.2

   We complement the growing literature on cryptocurrencies by performing the ﬁrst com-
prehensive study of technical trading in cryptocurrency markets in order to assess whether
technical trading rules offer predictive power and proﬁtability in various cryptocurrency mar-
kets. Technical trading is of particular interest in cryptocurrency markets for a number of
reasons. The trading approach has substantial documented success in the conventional cur-
rency markets and to, some extent, in many asset markets.3 Since cryptocurrency markets
have tended to follow strong trends since their inception, we have some prior that technical
trading rules may be beneﬁcial in cryptocurrency markets. In addition, the relative lack of
information relevant for performing fundamental analysis on cryptocurrencies may elevate

1 Financial Times (2018) https://www.ft.com/content/c8a47b42-11d4-11e8-8cb6-b9ccc4c4dbbb.
2 For an up-to-date review of the literature on cryptocurrencies, see Corbet et al. (2019).
3 For instance, Brock et al. (1992), Sullivan et al. (1999), Shynkevich (2012), Neely et al. (2014), Shynkevich
(2016) amongst others explained below.

123


---

Annals of Operations Research (2021) 297:191–220  193

Fig. 1 Time-series graphs of the prices of the prices of the cryptocurrencies employed in this study

the relative importance of technical approaches. This is because cryptocurrencies have no
fundamentals to examine and arguably have no intrinsic value. Therefore investors cannot
study, for example, the balance sheet or dividend forecasts to forecast future prices and
therefore have to rely on past price behaviour as a signal of future behaviour, which is the
fundamental concept behind technical trading.

   The only paper to our knowledge that examines technical trading in cryptocurrency mar-
kets is Detzel et al. (2018), who show that the 5- to 100-day moving average rule, both in- and
out-of-sample, offers predictive power to investors. They also show that trading strategies
based on these rules generate substantial alphas, utility and Sharpe ratios while signiﬁcantly
reducing the severity of drawdowns relative to a buy-and-hold position in Bitcoin. However
this paper examines just one type technical trading rule while there are many different types
of technical trading rules, with many different parameterizations. Investors have been shown
to use a number of different technical trading rules and therefore we further the literature by
studying a range of the most popular technical trading rules. Further although the Bitcoin
market is the largest, other cryptocurrency markets have been gaining attention that should
not be ignored since the growth of interest in the non-Bitcoin cryptocurrencies have grown
exponentially over the last few years.

   We study daily data from four different cryptocurrencies, namely Bitcoin, Litecoin,
Ethereum and Ripple, for the longest data period available for each individual cryptocur-
rency. We consider a range of ﬁve different classes of technical trading rules (similar to Hsu
et al. 2016), in which we examine a number of different parameters. As noted by Shynkevich
(2012), choosing too few rules can cause biases in statistical inference due to data mining.
On the other hand, using too many irrelevant rules can reduce the test power. We therefore
look for a balance and select a fairly large variety of reasonable parameters within the ﬁve
most popular families for a combined number of 14,919 trading rules. We employ a range
of performance metrics to assess the returns from technical trading, including a number of

                                                              123


---

194  Annals of Operations Research (2021) 297:191–220

risk-adjusted measures as well as the breakeven costs. Since we examine a number of dif-
ferent rules, we face the real possibility of data-snooping bias where the large number of
hypotheses tested means that the likelihood of a rejecting the null hypothesis of each trading
rule (making a Type I error) is quite high. To safeguard against this issue, we ﬁrst calculate the
individual bootstrapped p-values of each technical trading by comparing the actual p-value
to 1000 stationary bootstrapped p-values following the method of Sullivan et al. (1999). We
then use these individual bootstrapped p-values and adopt a number of approaches to control
for multiple hypothesis testing, namely the family-wise error rate (F W E R) and the false dis-
covery rate (F D R).4 Our results show that technical trading rules do offer predictive power
in cryptocurrency markets where the average annualized return for each family of technical
trading rule is statistically signiﬁcant at the 5% level for each cryptocurrency. Our results
are robust to risk-adjusted measures and the breakeven transaction costs of the majority of
rules examined are substantially higher than those found in cryptocurrency markets. After
accounting for data-snooping via various multiple hypothesis testing procedures, a large
proportion of technical trading rules still report signiﬁcant returns indicating the predictive
power and proﬁtability of technical trading in cryptocurrency markets. More importantly
however, we show that implementing technical trading rules signiﬁcantly reduces the poten-
tial drawdowns faced by the buy-and-hold and therefore protects investors from the lengthy
and severe drawdowns associated with cryptocurrency markets. Finally, we show that Bitcoin
does not offer any positive returns in the out-of-sample period, but the other cryptocurrencies
do offer positive returns and relatively highly Sharpe and Sortino ratios.

   The success of technical trading rules to generate consistent proﬁts has been an ongoing
debate in the academic literature. Practitioners have been found to use technical analysis
extensively, with Smith et al. (2016) showing that 21.6% of live hedge funds use technical
analysis while Menkhoff (2007) reports that technical analysis is widespread in the foreign
exchange market. Yet, the academic literature has heavily scrutinized the performance of
technical analysis since it provides evidence against one of the most respected theories in
ﬁnance, the efﬁcient market hypothesis. Weak form market efﬁciency states that all available
price information must be reﬂected in security prices and therefore the use of technical
analysis must be futile. Since the foreign exchange market is where technical analysis is
particularly widely used, studies have been plentiful and long indicated proﬁt opportunities
(for instance Poole 1967; Sweeney 1986; Levich and Thomas 1993; Neely et al. 1997; Gencay
1999; Qi and Wu 2006). This literature shows that simple technical trading rules on dollar
exchange rates provided 15 years of positive, risk-adjusted returns during the 1970s and
1980s before those returns were extinguished (Olson 2004). In a comprehensive study, Hsu
et al. (2016) study a large-scale study of technical trading rules in the foreign exchange
market over 45 years in 30 developed and developing markets and ﬁnd some evidence of
substantial predictability and excess proﬁtability in both developed and developing markets.
Zarrabi et al. (2017) show that from 1994 to 2014, technical trading rules are proﬁtable in
six currencies quoted in U.S. dollars, however they are not consistently proﬁtable.

   The foreign exchange market is not the only market to report signiﬁcant results from
employing technical trading rules. In equity markets, Brock et al. (1992) show that technical
trading provides signiﬁcant predictability over 90 years for the Dow Jones Industrial Average,
while Sullivan et al. (1999) and White (2000) show that the ﬁndings of Brock et al. (1992)
are not due to data-snooping. Many other papers have also reported signiﬁcant results for
technical trading in equity markets, such as Shynkevich (2012), Han et al. (2013) and Neely
et al. (2014). There is also evidence of signiﬁcant results from technical trading in commodity

4 See Harvey and Liu (2014) for more details on the issue of multiple hypothesis testing.

123


---

Annals of Operations Research (2021) 297:191–220  195

futures markets (Miffre and Rallis 2007; Szakmary et al. 2010; Narayan et al. 2015; Han et al.
2016), commodity spot markets (Batten et al. 2018; Psaradellis et al. 2019), bond markets
(Shynkevich 2016) and commodity ETFs (Hudson et al. 2017). Despite these ﬁndings, there is
no clear consensus on the predictability of technical trading rules in the literature, with many
papers indicating that technical trading rules do not offer any predictive power, especially once
transaction costs have been accounted for (for instance Bessembinder and Chan 1998; Allen
and Karjalainen 1999; Marshall et al. 2008a, b; Bajgrowicz and Scaillet 2012; Yamamoto
2012; Urquhart et al. 2015 ; Batten et al. 2018).

   Therefore this paper offers a number of important contributions to the literature. Firstly,
this is the ﬁrst paper to provide a large-scale study of the performance of technical trading
rules in cryptocurrencies. Although previous research has focused on a wide range of other
ﬁnancial assets only one paper (Detzel et al. 2018) focuses on cryptocurrencies and that paper
only investigates the Bitcoin cryptocurrency while we provide a comprehensive investigation
of a number of major cryptocurrencies. Secondly, we employ a wide-range of technical
trading rules to provide a thorough investigation of the performance of technical rules in
cryptocurrency markets. We also employ risk-adjusted performance measures as well as
compute breakeven transaction costs. Third, to safeguard against data-snooping we employ
a number of multiple hypothesis tests. Finally, we study the in-sample and out-of-sample
performance of technical trading rules in cryptocurrencies to safeguard against any data-
mining issues.

   The rest of the paper is organized as follows. Section 2 discusses the dataset used in this
study and provides descriptive statistics, while Sect. 3 describes the various technical trading
rules that we implement. Section 4 outlines the various performance metrics considered in
order to assess the performance of our rules while Sect. 5 sets out the data-snooping measures
employed in this study. Section 6 reports the empirical results while Sect. 7 provides a
summary and the conclusion.

2 Data

We employ daily Bitcoin prices from two providers for robustness purposes, namely Coin-
Desk and Bitstamp. CoinDesk represents an average of Bitcoin prices across leading global
exchanges that meet criteria speciﬁed by CoinDesk. These criteria include that the exchange
must serve an international customer base, must provide a bid-offer spread for an immediate
sale (offer) and an immediate purchase (bid), while also the minimum trade size must be less
than $1500 USD. Also, the daily trading volume must meet minimum acceptable levels as
determined by CoinDesk while the exchange must represent at least 5% of the total 30-day
cumulative volume for all of the exchanges included in the CoinDesk price. We also study
an actual exchange Bitcoin price, Bitstamp, which is one of the ﬁrst, most popular and liquid
Bitcoin exchanges (Brandvold et al. 2015), is based in the UK and is considered to be a rather
safe exchange by market participants around the world (Bouri et al. 2017). For the other cryp-
tocurrencies, we obtain daily data from www.CoinMarketCap.com for Litecoin, Ethereum
and Ripple, which are the largest and most liquid cryptocurrencies in the market.5 We study
each cryptocurrency for the maximum period possible to ensure our results provide a com-
plete picture of the performance of technical analysis in these cryptocurrencies. Specially,
we study CoinDesk’s Bitcoin price from 18th July 2010, Bitstamp from 1st December 2012,

5 www.CoinMarketCap.com has been employed previously in the literature to examine cryptocurrencies other
than Bitcoin, such as Ciaian et al. (2018).

                                                              123


---

196                                  Annals of Operations Research (2021) 297:191–220

Table 1 Descriptive statistics of the returns of Bitstamp, CoinDesk, Ethereum, Ripple and Litecoin from the
start of available data to the 31st December 2017

Cryptocurrency Mean  SD      Max     Min       Skewness Kurtosis Obs

CoinDesk  0.0061     0.0592  0.5289  − 0.3883  0.8328  12.1985  2735
Bitstamp  0.0049     0.0481  0.4014  − 0.4852  0.0693  14.2082  2217
Litecoin  0.0049     0.0769  1.2910  − 0.4019  5.0661  67.6347  1710
Ripple    0.0070     0.0927  1.7937  − 0.4600  6.3377  97.9744  1624
Ethereum  0.0098     0.0799  0.5070  − 0.7292  0.2199  13.1442   877

Litecoin from 28th April 2013, 28th April 2013, Ripple from 4th August 2013 and Ethereum
from 7th August 2015. All prices end on 31st December 2017. All markets trade 24 hours a
day 7 days a week and therefore we include all observations during the day including week-
ends and holidays and have a complete time-series. Figure 1 presents the time-series graph
of each cryptocurrency over time for the sample periods chosen in this study and each show
the dramatic rise in the price of each cryptocurrency and therefore also the large volatility.
We employ simple returns such that:

                             rt =  Pt − Pt−1                    (1)
                                      Pt −1

where Pt is the price of the cryptocurrency at time t and Pt−1 is the price of the cryptocur-
rency at time t − 1.6 Table 1 reports the descriptive statistics of the returns of the various
cryptocurrencies where we ﬁnd that the all cryptocurrencies have a positive mean return, with
Ethereum the largest and Litecoin the smallest where Ethereum has a mean return double
that of Bitstamp and Litecoin. Ripple is the most volatile cryptocurrency while Bitstamp is
the least volatile. The maximum and minimum values for each cryptocurrency document
the extreme returns that can be found with these cryptocurrencies. All cryptocurrencies are
positively skewed, reﬂecting the general upward trend in cryptocurrency prices.7 All cryp-
tocurrencies exhibit excess kurtosis indicating the leptokurtic nature of these returns. Litecoin
and Ripple are the most heavily positively skewed and have the largest excess kurtosis of all
cryptocurrencies. Therefore Table 1 reﬂects the nature of cryptocurrency markets and how
they are quite different to traditional ﬁnancial assets.

3 Technical trading rules

Taylor and Allen (1992) note that technical analysis can be separated into two distinct cate-
gories, namely the qualitative form and the quantitative form. The qualitative form is where
charts are analyzed and attempts are made to identify patterns in the data while the quan-
titative form is the analysis of past charts through time-series analysis to construct trading
signals. The main difference between the two types is that, given a certain trading rule, quan-
titative technical analysis is completely objective and every individual should come to the
same conclusion while qualitative technical analysis is subjective and individuals may come
to different conclusions from the same chart.

6 We use simple returns in order to assess the proﬁtability of technical trading rules from the perspective of
an investor, similar to Bajgrowicz and Scaillet (2012).
7 This is unlike the vast majority of traditional assets which generally have negative skewness.

123


---

Annals of Operations Research (2021) 297:191–220                                       197

   We follow Hsu et al. (2016) and study ﬁve classes of technical trading rules that are
commonly used by traders and examined in the literature. The ﬁrst class is moving average
rules (which are the most examined class of technical trading rule in the literature) which
attempt to ride trends and identify imminent breaks by examining moving averages, and are
quite similar to the time-series momentum effect, ﬁrst outlined by Moskowitz et al. (2012)
with a correlation of returns between the two in excess of 0.80 (see Marshall et al. (2017) for a
comparison between time-series momentum and moving average rules). The second class of
rules we study are ﬁlter rules which attempt to follow trends by buying (selling) whenever the
price has increased (decreased) by a given percentage. The third class are support-resistance
trading rules, which create support or resistance bounds around the price which if they breach,
indicates further movement in the same direction. The fourth class we study are oscillator
trading rules, which attempt to identify overbought (oversold) assets and therefore anticipate
the imminent market correction. The ﬁnal class of rule studied is the channel breakout rules
which identify time-varying support and resistance levels which, once breached, indicate
further movement in the same direction.

   The choice of parameters to employ in these rules is quite important since different param-
eters may generate quite contrasting returns. Therefore we examine a number of different
variants of each class of trading rule, and therefore obtain a very large number of different
possible rules. “Appendix” presents more details of the different variants of each of the class
of rules as well as the various parameterizations employed in this study. In total, we study
14,919 technical trading rules.

4 Performance metrics

The return from the jth technical trading in each cryptocurrency market is deﬁned as;

R j,t = S j,t−1rt                                                                      (2)

where S j,t−1 denotes the position guided by j th technical trading rule which is determined
by historic prices tracking back from the closing spot rate of period t − 1. S j,t−1 either
takes the value of 1 where we go long in the cryptocurrency, −1 where we go short in the
cryptocurrency or 0 where we are neutral. If we are neutral, we are out of the market and
invested in cash.8

   Any analysis of trading strategies needs to be concerned with transaction costs since if the
returns from a trading strategy are not positive after taking account of transaction costs, the
strategy is worthless to an investor. This is especially important since many papers have found
that technical trading rules are proﬁtable for investors but once transaction costs are accounted
for, many rules are no longer proﬁtable. Lintilhac and Tourin (2017) show that transaction
costs on Bitcoin is around 50 basis points. However the actual transaction costs may be
very different on different exchanges, and since we study four different cryptocurrencies,
transaction costs across cryptocurrency markets may differ. Therefore we report the breakeven
transaction costs in order to determine the magnitude of transaction costs that would make
technical trading returns zero.

8 We invest in cash if we are not long or short in the cryptocurrency, meaning our results are based purely on
the beneﬁts of employing technical analysis on Bitcoin since we take no returns from the risk-free rate.

                                                              123


---

198                    Annals of Operations Research (2021) 297:191–220

   The ﬁrst performance metric we report is the daily mean return of the jth technical trading
rule which is deﬁned as;

              1  T
              n
     R¯ j  =           R j,t  (3)

                 t =1

where R¯ j is the mean return. This is the simplest performance measure and quantiﬁes the
average return from each trade of each technical trading rule. However, an issue with this

measure is that it does not take into account the riskiness of the trading rule in terms of

volatility of returns. Therefore we also calculate the Sharpe ratio which is the standard

performance metric in the ﬁnance industry and measures units of average excess return per

unit of risk as measures by the standard deviation of excess returns. The Sharpe ratio of the
jth technical trading rue is deﬁned as;

     SRj   =     R¯ j − r f   (4)
                    σj

where r f is the daily US risk free rate which is calculated from the monthly U.S. risk-free
obtained from the Kenneth French data library and σ j is the standard deviation of excess
returns generated by the jth trading rule.9 However an issue with the Sharpe ratio is that it

includes downside volatility as well as upside volatility, with the same weighting. Investors

may only be interested in the downside risk as the upside provides them with greater returns.

Consequently we also calculate the Sortino ratio which of the jth technical trading rue is

deﬁned as;

     SOj   =     R¯ j − r f   (5)
                   σn, j

where σn, j is the standard deviation of negative excess returns generated by the jth trading
rule and again we annualized the Sortino ratio. Our ﬁnal performance metric is the Calmar
ratio, which is an important indicator for investment banks as well as the hedge fund indus-
try (Psaradellis et al. 2019).10 The Calmar ratio calculates the average annual return of an
investment per unit of maximum drawdown and is especially useful for practitioners who
employ momentum strategies that can suffer considerable drawdowns. The Calmar ratio of
the jth technical trading rue is deﬁned as;

     CRj      =    R¯ j       (6)
                 MDDj

where M D Dd, j is the maximum drawdown of the excess returns generated by the jth trading
rule.

5 Data-snooping

Data snooping bias is a real issue whenever any trading strategy is implemented since exam-
ining just the mean excess return across rules is not sufﬁcient. Searching among a range of
competing trading rules implicitly involves increasing the number of hypotheses tested as

9 Kenneth French data sets can be found at http://mba.tuck.dartmouth.edu/pages/faculty/ken.french/
data_library.html.
10 The Calmar ratio was developed by Young (1991) and stands for “California Managed Account Reports”.

123


---

Annals of Operations Research (2021) 297:191–220  199

poorly performing rules are disregarded. The problem of multiple hypothesis testing arises
from the fact that as we increase the number of hypotheses being tested, we also increase
the likelihood of a rare event and therefore, the likelihood of incorrectly rejecting the null
hypothesis of each trading rule (making at Type I error). In our case, after testing n number of
trading rules, a skeptic would argue that they would have been surprised if we had not found
any that performed extremely well.11 This is demonstrated by Chordia et al. (2018) who
create 2.1 million trading strategies and apply various multiple hypothesis testing techniques
to show the outperformance under single hypothesis testing are likely false. The surviving
strategies have no theoretical underpinnings and therefore p-hacking is a serious problem
and after correcting for it, outperforming trading strategies are very rare.

   We adopt two broad approaches to deal with multiple hypothesis testing, namely family-
wise error rate (FWER) and the false discovery rate (FDR).

5.1 FWER

The strictest multiple hypothesis test is to try and avoid any false rejections. This translates
to controlling the FWER, which is deﬁned as the probability of rejecting even one of the true
null hypothesis and therefore the FWER measures the probability of even one false discovery.
We implement two main FWER tests.

5.1.1 Bonferroni method

The Bonferroni method is a single-step procedure since all p-values are compared to a single
critical value. This critical p-value is α/M, where α is the critical value chosen and M is
number of rules examined. For a large number of rules, this adjustment leads to an extremely
small critical p-value which makes it very conservative and leads to a loss of power. The
lack of power is due to the fact that is implicitly treats all test statistics as independent and
therefore ignores cross-correlation that is bound to be present in the technical trading rules
employed in this study.

5.1.2 Holm method

The Holm method is a stepwise adjustment that that rejects the null hypothesis of no outper-
forming rules if pi ≤ α/(M − i + 1) for i = 1, . . .. Compared to the Bonferroni method,
the Holm method becomes less strict for large p-values. Thus the Holm method typically
rejects more hypotheses and is more powerful than the Bonferroni method. However, it also
does not take into account the dependence structure of the individual p-values and is very
conservative.

5.2 FDR

Rather than controlling for the number of false rejections, we can control for the proportion
of false rejections of the False Discovery Proportion (FDP). FDR measures and controls the
expected FDP among all discoveries where a multiple hypothesis testing method is said to
control FDR at level δ if F D R ≡ E(F D P) ≤ δ, where the level δ is user-deﬁned.

11 Or as Economics Nobel Laureate Ronald Coase put it, “if you torture the data long enough, it’ll confess to
anything”.

                                                              123


---

200                                                  Annals of Operations Research (2021) 297:191–220

5.2.1 BH method

One of the earliest FDR controlling methods is by Benjamini and Hochberg (1995) and is a
stepwise procedure that, assuming all individual p-values are ordered from smallest to largest
and deﬁning:

                         j∗ = max j : p ≤ j × δ                                             (7)
                                                     M

where we reject all hypothesis H1, H2, . . . , H j . This is a step-up method that starts with
examining the least signiﬁcant hypothesis and moves up to more signiﬁcant test statistics.

5.2.2 BY method

Although Benjamini and Hochberg (1995) show that their method measures FDR if the p-

values are mutually independent, Benjamini and Yekutieli (2001) show that a more general

control of FDR under a more arbitrary dependence structure of p-values can be achieved by
replacing the deﬁnition of j∗ with:

                         j∗ = max j : p ≤ j × δ                                             (8)
                                                     M × CM

where the constant CM =  M     1/i  ≈  l og( M )  +  0.5.  However  this  method  is  less  powerful
                         i =1

than the B H method and is still very conservative.

We employ these four multiple hypothesis testing procedures on the individual p-values

of each trading rule. Consistent with Bajgrowicz and Scaillet (2012), to acquire individual

p-values, we follow the re-sampling procedure of Sullivan et al. (1999). We employ the

stationary bootstrap method of Politis and Romano (1994) to resample the returns of each

strategy, where the corresponding test statistic for each bootstrap series of returns is calculated
by comparing the original p-value with the bootstrapped p-values.12

6 Empirical results

6.1 Initial results

Table 2 reports the summary of the performance of the technical trading rules across all
cryptocurrencies. We present the average result for all parameterizations of each technical
trading rule where we show that on average, all ﬁve classes of technical trading rules generate
signiﬁcant annualized returns for all cryptocurrencies studied. For all cryptocurrencies and
technical trading rules, the average return from a buy signal is positive and statistically
signiﬁcant while the average return from a sell signal is mostly negative indicating that the
positive returns from technical trading in cryptocurrencies comes from the buy signals rather
than the sell signals. Across all cryptocurrencies, the ﬁlter rule and the channel breakout
rule performed best, generating the highest annualized returns which is as high as 16.45%
for Ripple. The results reported in Table 2 only show the returns but the riskiness of the
returns are very informative for investors. Therefore we report a number of metrics allowing
for risk in Table 3 where we ﬁnd that the all of them are greater than zero indicating that

12 The block length is equal to 0.1 and the number of bootstrap realizations is set to 1000, consistent with
previous studies.

123


---

     Table 2 The performance of the technical trading rules over the full sample period for each cryptocurrency                                   Annals of Operations Research (2021) 297:191–220

     Technical trading rule   No.Buys  No.Sells  Ave Buy Return (%)  Ave Sell Return (%)                         Ave Return (%)   Ann.Return (%)

     Panel A: CoinDesk        1114.80  546.59    0.42∗∗∗             − 0.02                                      0.40∗∗∗          7.72∗∗∗
     Moving average rule      2235.67  104.60    0.55∗∗∗             − 0.01                                      0.54∗∗∗         10.24∗∗∗
     Filter rule                                 0.19∗∗∗             − 0.02                                      0.17∗∗∗
     Support-resistance rule   333.03   85.09    0.41∗∗∗             − 0.02                                      0.38∗∗∗          3.33∗∗∗
     Oscillator rule           858.04  265.08    0.54∗∗∗             − 0.01                                      0.53∗∗∗          7.34∗∗∗
     Channel breakout rule    2075.14  135.36                                                                                    10.11∗∗∗
     Panel B: Bitstamp                           0.33∗∗∗             − 0.03                                      0.30∗∗∗
     Moving average rule       899.11  432.58    0.43∗∗∗             − 0.01                                      0.42∗∗∗          5.82∗∗∗
     Filter rule              1788.75   80.65    0.16∗∗∗             − 0.02                                      0.14∗∗∗          7.97∗∗∗
     Support-resistance rule   282.81   62.76    0.29∗∗∗             − 0.03                                      0.27∗∗∗          2.63∗∗∗
     Oscillator rule                   161.15    0.42∗∗∗             − 0.01                                      0.41∗∗∗          5.07∗∗∗
     Channel breakout rule     623.26  109.92                                                                                     7.89∗∗∗
                              1642.09

123                                                                                                                                               201


---

123  Table 2 continued                                                                                                                                                               202
     Technical trading rule
                              No.Buys  No.Sells  Ave Buy Return (%)  Ave Sell Return (%)  Ave Return (%)  Ann.Return (%)

     Panel C: Litecoin         478.50  530.66    0.36∗∗∗               0.00               0.35∗∗∗          6.74∗∗∗                                                                   Annals of Operations Research (2021) 297:191–220
     Moving average rule      1291.54  109.95    0.48∗∗∗               0.00               0.48∗∗∗          9.18∗∗∗
     Filter rule                        71.52    0.12∗∗∗             − 0.02               0.10∗∗∗          1.96∗∗∗
     Support-resistance rule   123.48  257.41    0.31∗∗∗               0.00               0.31∗∗∗          5.85∗∗∗
     Oscillator rule           300.87  153.71    0.47∗∗∗               0.01               0.48∗∗∗          9.21∗∗∗
     Channel breakout rule    1162.34
     Panel D: Ripple                   576.14    0.48∗∗∗             − 0.01               0.47∗∗∗          8.89∗∗∗
     Moving average rule       425.25  139.85    0.64∗∗∗               0.00               0.64∗∗∗         12.30∗∗∗
     Filter rule              1191.46  105.24    0.26∗∗∗                                  0.25∗∗∗
     Support-resistance rule           271.30    0.42∗∗∗             − 0.02               0.42∗∗∗          4.73∗∗∗
     Oscillator rule           135.52  184.69    0.63∗∗∗               0.00               0.64∗∗∗          7.94∗∗∗
     Channel breakout rule     282.21                                  0.01                               12.21∗∗∗
     Panel E: Ethereum        1090.53  153.57    0.65∗∗∗                                  0.59∗∗∗
     Moving average rule                33.02    0.88∗∗∗             − 0.06               0.86∗∗∗         11.32∗∗∗
     Filter rule               369.60   33.71    0.24∗∗∗             − 0.02               0.20∗∗∗         16.45∗∗∗
     Support-resistance rule   697.17   91.31    0.52∗∗∗             − 0.03               0.49∗∗∗
     Oscillator rule           104.46   42.50    0.85∗∗∗             − 0.03               0.84∗∗∗          3.85∗∗∗
     Channel breakout rule     261.87                                − 0.02                                9.40∗∗∗
                               663.41                                                                     15.99∗∗∗

     “No.Buys” and “No.Sells” denote the number of buy and sell signals generated while the “Ave Buy Return” and “Ave Sell Return” denote the average daily buy and sell returns.
     “Ave Return” denotes the average daily return of the trading rules while “Ann.Return” refers to the average annualized return from each trading signal. ***, ** and * indicate
     signiﬁcance at the 1%, 5% and 10% levels respectively


---

     Table 3 The risk adjusted performance of the technical trading rules over the full sample period for each cryptocurrency, where we report the Sharpe, Annualized Sharpe,  Annals of Operations Research (2021) 297:191–220
     Adjusted Sharpe, Sortino, Annualized Sortino and the Calmar ratios

     Technical trading rule   Sharpe  Ann. Sharpe  Adj. Sharpe  Sortino  Ann. Sortino  Calmar

     Panel A: CoinDesk        0.0039  0.0751       0.0763       0.1378   2.6324        2.9415
     Moving average rule      0.0053  0.1009       0.1022       0.1626   3.1060        3.7812
     Filter rule              0.0015  0.0286       0.0291       0.0867   1.6559        1.2753
     Support-resistance rule  0.0037  0.0713       0.0725       0.1487   2.8409        2.8481
     Oscillator rule          0.0052  0.0995       0.1008       0.1619   3.0927        3.9109
     Channel breakout rule
     Panel B: Bitstamp        0.0029  0.0553       0.0553       0.1162   2.2206        1.9806
     Moving average rule      0.0041  0.0778       0.0774       0.1435   2.7411        2.8246
     Filter rule              0.0010  0.0189       0.0257       0.0883   1.6875        0.9897
     Support-resistance rule  0.0025  0.0480       0.0479       0.1297   2.4775        1.9336
     Oscillator rule          0.0040  0.0769       0.0765       0.1433   2.7373        2.9659
     Channel breakout rule

123                                                                                                                                                                            203


---

123  Table 3 continued                                                                          204

     Technical trading rule   Sharpe  Ann. Sharpe  Adj. Sharpe  Sortino  Ann. Sortino   Calmar  Annals of Operations Research (2021) 297:191–220

     Panel C: Litecoin        0.0034  0.0657       0.0691       0.1041   1.9891         1.3079
     Moving average rule      0.0047  0.0906       0.0960       0.1359   2.5957         1.8565
     Filter rule              0.0007  0.0132       0.0139       0.0495   0.9461         0.4557
     Support-resistance rule  0.0030  0.0573       0.0606       0.1137   2.1719         1.4240
     Oscillator rule          0.0048  0.0908       0.0963       0.1370   2.6170         2.0260
     Channel breakout rule
     Panel D: Ripple          0.0046  0.0876       0.0935       0.1271   2.4276         2.2358
     Moving average rule      0.0064  0.1220       0.1304       0.1648   3.1491         3.1258
     Filter rule              0.0023  0.0447       0.0484       0.0948   1.8116         1.4682
     Support-resistance rule  0.0041  0.0778       0.0831       0.1318   2.5189         2.0657
     Oscillator rule          0.0063  0.1211       0.1293       0.1638   3.1286         3.2246
     Channel breakout rule
     Panel E: Ethereum        0.0058  0.1115       0.1134       0.1676   3.2017         8.2456
     Moving average rule      0.0085  0.1633       0.1673       0.2346   4.4822        16.2931
     Filter rule              0.0018  0.0351       0.0358       0.0796   1.5214
     Support-resistance rule  0.0048  0.0919       0.0935       0.1601   3.0591         1.9094
     Oscillator rule          0.0083  0.1586       0.1624       0.2279   4.3532         6.0633
     Channel breakout rule                                                             15.9528


---

Annals of Operations Research (2021) 297:191–220  205

technical trading in cryptocurrencies outperforms the risk-free rate. We ﬁnd that the Sortino
ratio is much higher than the Sharpe and adjusted Sharpe ratios indicating that the riskiness
from downside movements in returns is very limited. This is also supported by the Calmar
ratio which, in each case, is quite large. Therefore our results show that on average, all
classes of technical trading trading rules generate signiﬁcant returns which provide favorable
risk-adjusted metrics.

   However it may be the case that not all of the different parameterizations of the technical
trading rules will generate positive and signiﬁcant returns. Therefore for each rule, we report
the percentage of buy, sell and overall signals that produce positive and signiﬁcant returns
and present the results in Table 4. Over 95% of technical trading rules generate positive buy
returns in CoinDesk and Bitstamp, while over 90% of rules generate positive buy returns
in Litecoin and Ripple. The vast majority of rules generate signiﬁcant buy returns across
all technical rule classes and across cryptocurrencies. The percentage of sell returns that
generate positive returns is somewhat lower, ranging between only 1.97% for the Oscillator
rule in CoinDesk, to 52.47% for the moving average rule in Litecoin. This suggests that only
some of the parameterizations of each rule do generate positive returns from a sell signal.
Also, we ﬁnd that only a very small percentage of sell return signals do generate signiﬁcant
returns, with 15 out of the 20 technical trading rule classes across all cryptocurrencies not
having any rules that generate a signiﬁcant sell return after sell signals. The ﬁnal two columns
report the statistics for the overall returns and show that the vast majority of rules generate
positive returns while over 50% of them generate signiﬁcant returns at the 5% level, with the
exception of the support-resistance rule for Litecoin, Ripple and Ethereum. Therefore the
results in Table 4 show that although not all the technical trading rules generate positive and
signiﬁcant returns, quite a few still do generate signiﬁcant returns for investors.

   Given that some of the trading rules do perform well and some not so well, Table 5
reports the best and worst performing rules regarding annualized return, Sharpe and Sortino
ratios.13 Clearly the worst performing rules generate annualized returns ranging from 2.68
to − 3.90%, with negative Sharpe and Sortino ratios. However the best performing rules
reported in the ﬁnal three columns show substantial returns for investors. For example, the
highest annualized return in CoinDesk is 13.42% while the highest for Ethereum is 22.15%.
The annualized Sharpe and Sortino ratios are also quite large indicating the risk-adjusted
beneﬁts of technical trading in cryptocurrencies. Therefore if investors can choose the best
performing rules, then there are return making opportunities in applying technical trading
rules to cryptocurrency markets.

6.2 Transaction costs

Up to this point, the analysis has assumed zero transaction costs but in practice these may
be signiﬁcant, even when trading cryptocurrencies. Indeed, a technical trading rule may
predict cryptocurrency movements in the sense of generating signiﬁcant returns but still
not be proﬁtable once the excess returns are adjusted for transaction costs (Timmermann and
Granger 2004). Transaction costs in cryptocurrencies differ depending on the cryptocurrency
traded and the exchange traded. Lintilhac and Tourin (2017) shows that the transaction fee
per number of Bitcoins is $0.0025 while the bid-ask spread is 0.005 as a fraction of the price
is USD. However it is difﬁcult to accurately estimate the transaction costs of CoinDesk since
it is an average of the leading global exchanges of Bitcoin, while the transaction costs of the

13 All of the other performance metrics are not included to conserve space but are available from the corre-
sponding author upon request.

                                                              123


---

123  Table 4 The percentage of successful technical rules for each cryptocurrency where we report the percentage of technical trading rules with positive buy (sell) returns and the  206
     percentage of those that are statistically signiﬁcant at the 5% level

     Technical trading rule   % + Buy Ret.  % Sig. Buy Ret.  % + Sell Ret.  % Sig. Sell Ret.  % + Ret.  % Sig. Ret.

     Panel A: CoinDesk         96.71        88.69            27.53          0.01               96.61    87.40
     Moving average rule      100.00        99.68                                             100.00    98.84
     Filter rule                            66.56            18.20          0.00                        58.10
     Support-resistance rule   95.03        96.05                                              92.49    95.44
     Oscillator rule           99.63        98.66            7.62           0.00               99.63    97.26
     Channel breakout rule    100.00                                                           99.74
     Panel B: Bitstamp                      88.69            1.97           0.00                        87.40
     Moving average rule       96.70        99.15                                              96.61    98.31
     Filter rule              100.00        71.96            29.33          0.00               99.68    62.12
     Support-resistance rule                96.17                                              95.45    95.56
     Oscillator rule           97.04        98.66            27.52          0.01               99.75    97.26
     Channel breakout rule     99.75                                                           99.74
     Panel C: Litecoin        100.00        78.20            21.69          0.11                        69.30
     Moving average rule                    97.46                                              96.15    92.80
     Filter rule               95.60        32.17            4.87           0.00               99.47    20.95
     Support-resistance rule   99.79        79.26                                              83.28    74.07
     Oscillator rule           90.79        94.84            1.98           0.00               95.19    90.50
     Channel breakout rule     95.19                                                           98.72
                               99.45                         29.33          0.00

                                                             52.47          0.09                                                                                                      Annals of Operations Research (2021) 297:191–220

                                                             51.96          0.00

                                                             14.71          0.00

                                                             45.19          0.00

                                                             70.54          0.04


---

     Table 4 continued        % + Buy Ret.  % Sig. Buy Ret.  % + Sell Ret.  % Sig. Sell Ret.  % + Ret.  % Sig. Ret.                                                                     Annals of Operations Research (2021) 297:191–220
     Technical trading rule

     Panel D: Ripple           96.92        84.44            38.73          0.31               96.45    79.26
     Moving average rule      100.00        99.79                                             100.00    99.68
     Filter rule                            46.56            37.46          0.32                        39.89
     Support-resistance Rule   94.29        80.39                                              92.38    76.33
     Oscillator rule           99.14        99.55            15.24          0.00               99.14    98.60
     Channel breakout rule    100.00                                                          100.00
     Panel E: Ethereum                      85.17            33.17          0.00                        80.92
     Moving average rule       96.09        98.84                                              94.73    97.35
     Filter rule              100.00        39.01            52.40          0.70              100.00    28.22
     Support-resistance rule                80.02                                                       75.96
     Oscillator rule           87.63        96.77            16.37          0.01               86.89    94.88
     Channel breakout Rule     98.40                                                           98.40
                               99.77                         20.74          0.00               99.66

                                                             14.16          0.00

                                                             14.06          0.00

                                                             25.56          0.08

     We also report the percentage of technical trading rules that generate positive returns, as well as the percentage of rules that produce signiﬁcant returns at the 5% signiﬁcance
     level

123                                                                                                                                                                                     207


---

123  Table 5 The performance of the best and worst technical trading rules for each technical trading rule class studied                               208

     Technical trading rule   Low. Ret. (%)  Low. Sharpe  Low. Sortino  High. Ret. (%)                                    High. Sharpe  High. Sortino

     Panel A: CoinDesk        − 1.56         − 0.1876     − 0.9431      12.89                                             0.1275        3.5891
     Moving average rule        0.14         − 0.0022     − 0.0686      12.71                                             0.1256        4.4093
     Filter rule                             − 0.0310     − 0.6051      11.50                                             0.1135        4.4346
     Support-resistance rule  − 0.82         − 0.0062     − 0.0829      11.68                                             0.1154        4.4654
     Oscillator rule          − 0.11         − 0.0006     − 0.0228      13.42                                             0.1328        4.0655
     Channel breakout rule    − 0.98
     Panel B: Bitstamp                       − 0.1754     − 1.3216       9.49                                             0.0932        5.5326
     Moving average rule      − 2.12         − 0.0204     − 0.9523      10.71                                             0.1054        3.6829
     Filter rule              − 1.66         − 0.1754     − 0.9331                                                        0.0858        4.1687
     Support-resistance rule  − 1.40         − 0.0038     − 0.3844       8.76                                             0.0856        4.1410
     Oscillator rule                         − 0.0209     − 0.9789       8.75                                             0.1071        3.7081
     Channel breakout rule      0.36                                    10.88
                              − 1.71

                                                                                                                                                       Annals of Operations Research (2021) 297:191–220


---

     Table 5 continued        Low. Ret. (%)  Low. Sharpe  Low. Sortino                                         High. Ret. (%)  High. Sharpe  High. Sortino  Annals of Operations Research (2021) 297:191–220
     Technical trading rule
                                                                                                               12.09           0.1199        4.9047
     Panel C: Litecoin        − 3.07         − 0.0718     − 1.4312                                             12.73           0.1263        3.6305
     Moving average rule      − 1.00         − 0.0118     − 0.5276                                             11.39           0.1128        3.4859
     Filter rule              − 2.99         − 0.0765     − 1.0944                                             10.46           0.1035        3.9360
     Support-resistance rule  − 1.14         − 0.0251     − 0.6743                                             12.59           0.1249        3.6916
     Oscillator rule          − 1.95         − 0.0321     − 1.0591
     Channel breakout rule                                                                                     20.51           0.2043        5.4383
     Panel D: Ripple          − 3.77         − 0.0626     − 0.8037                                             18.75           0.1866        4.7530
     Moving average rule        2.68           0.0239       0.9338                                             17.43           0.1734        4.7239
     Filter rule                                                                                               17.95           0.1787        4.5778
     Support-resistance rule  − 0.72         − 0.0192     − 0.6126                                             17.21           0.1712        4.8170
     Oscillator rule          − 0.63         − 0.0144     − 0.7068
     Channel breakout rule                                                                                     21.49           0.2138        6.5969
     Panel E: Ethereum          1.57           0.0119       0.5512                                             22.15           0.2203        5.9422
     Moving average rule                                                                                       18.72           0.1861        4.9685
     Filter rule              − 3.90         − 0.0414     − 1.4669                                             20.47           0.2035        5.3837
     Support-resistance rule    0.67         − 0.0108     − 0.4907                                             21.76           0.2164        5.8498
     Oscillator rule                         − 0.0195     − 1.1403
     Channel breakout rule    − 1.42         − 0.0227     − 1.0047
                              − 1.45         − 0.0108     − 0.4907
                              − 0.67

     We report the lowest and highest annualized return, annualized Sharpe ratio and annualized Sortino ratio

123                                                                                                                                                         209


---

210                                  Annals of Operations Research (2021) 297:191–220

Table 6 The number of new trades generated by the technical trading rules for each cryptocurrency, the
breakeven transaction costs in basis points and the percentage of rules that have greater breakeven transaction
costs than 50 basis points

Technical trading rule   No. trades  Breakeven TCs  % > 50 basis points

Panel A: CoinDesk        182.98       54.86         32.04
Moving average rule      294.22       66.41         32.38
Filter rule              223.65       11.42          0.00
Support-resistance rule  210.89       44.60         36.06
Oscillator rule          274.25       61.00         30.18
Channel breakout Rule
Panel B: Bitstamp        152.65       50.40         22.79
Moving average rule      238.43       57.51         28.15
Filter rule              184.06       11.89          0.95
Support-resistance rule  172.04       38.74         25.15
Oscillator rule          217.57       54.12         27.38
Channel breakout rule
Panel C: Litecoin        137.39       35.44         25.81
Moving average rule      237.13       30.66         19.68
Filter rule              121.38                      0.21
Support-resistance rule  134.73         7.88        24.44
Oscillator rule          214.77       38.42         17.97
Channel breakout rule                 30.42
Panel D: Ripple          128.55                     26.25
Moving average rule      242.44       36.01         19.15
Filter rule              135.45       33.59
Support-resistance rule  127.45       16.16          3.49
Oscillator rule          219.22       52.14         34.04
Channel breakout rule                 33.06         18.37
Panel E: Ethereum         68.39
Moving average rule       99.83       78.60         38.72
Filter rule               76.66      147.56         49.52
Support-resistance rule   69.12                      0.11
Oscillator rule           93.53         9.89        36.74
Channel breakout Rule                 50.05         47.35
                                     144.03

other cryptocurrencies may vary quite considerably over time. Therefore to avoid any bias
in our results, we report in Table 6 the average breakeven transaction costs in basis points,
along with the number of trades required. The number of trades are fairly constant within
each cryptocurrency, although the ﬁlter rule does generate the highest number of trades across
of cryptocurrencies. The breakeven transaction costs range 7.88 basis points for the support-
resistance rule in Litecoin to 147.56 basis points for the ﬁlter rule in Ethereum. If we focus on
CoinDesk and Bitstamp, the breakeven transaction costs are as high as 66.41 and 57.51 basis
points respectively. Lintilhac and Tourin (2017) report that the transaction costs for Bitcoin
is around 50 basis points and therefore also in Table 6 we report the percentage of technical
trading rules that offer breakeven transaction costs greater than 50 basis points. Each class

123


---

Annals of Operations Research (2021) 297:191–220                           211

Table 7 This table reports the annualized return, Sharpe, Sortino and Calmar ratios for the buy-and-hold
strategy in each cryptocurrency

          Ann.Return       Ann.Sharpe             Ann.Sortino      Calmar

CoinDesk  0.1167 (6.12%)   0.1153 (6.12%)         3.1996 (32.83%)  4.22019 (28.58%)
Bitstamp  0.0942 (4.96%)   0.0925 (4.86%)         3.0163 (32.14%)  3.4522 (32.72%)
Litecoin  0.0928 (11.49%)  0.0918 (41.30%)        2.4167 (51.26%)  1.3750 (57.64%)
Ripple    0.1339 (15.69%)  0.1330 (15.69%)        3.1768 (27.99%)  2.7796 (36.73%)
Ethereum  0.1875 (9.01%)   0.1864 (8.98%)         3.9645 (49.71%)  11.0426 (42.17%)

In brackets, we also report the percentage of technical trading rules that report returns higher than that of the
buy-and-hold strategy

of technical trading rule in each cryptocurrency all generate a substantial percentage of rules
that are greater than 50 basis points, with the exception of the support-resistance rule. For
instance, 36.06% of oscillator rules generate breakeven transaction costs greater than 50 basis
points for CoinDesk while 47.35% of channel breakout rules generate rules with breakeven
transaction costs greater than 50 basis points for Ethereum. Very few support-resistance
rules rules generate breakeven transaction costs greater than 50 basis points, indicating that
this family of technical trading rules are not very successful for all four cryptocurrencies.
Nevertheless, a large proportion of technical trading rules do generate breakeven transaction
costs greater than 50 basis points indicating that performance of technical trading rules in
cryptocurrencies are not wiped out by appropriate transaction costs.

6.3 Comparison to the buy-and-hold strategy

As shown in Fig. 1, cryptocurrencies have followed an upward trend over time, especially in
the most recent time period. Therefore a buy-and-hold strategy may have been quite successful
over the same sample period. Therefore in Table 7 we report the annualized return, annual-
ized Sharpe ratio, annualized Sortino ratio and Calmar ratio for the buy-and-hold strategies
for each cryptocurrency. In brackets, we also report the percentage of technical trading rules
that generate risk-adjusted returns greater than the buy-and-hold strategy. For each cryp-
tocurrency, we see that only a small proportion of rules generate annualized returns greater
than the buy-and-hold strategy. However once we examine the risk-adjusted metrics, we ﬁnd
that substantially more technical trading rules offer returns greater than the buy-and-hold
strategy, especially for the annualized Sortino and Calmar ratios, which both capture down-
side risk. This indicates that employing technical trading rules avoids the large, severe and
lengthy drawdowns associated with cryptocurrencies and offers investors smoother returns
than those that could have been gained from the simple buy-and-hold strategy. Therefore we
show that if investors want to limit their risk exposure to cryptocurrency volatility, they could
employ technical trading rules to smooth their future returns.

6.4 MHT adjustment

So far, we have shown that technical trading rules do offer predictive power to investors in
ﬁve cryptocurrency markets. However as mentioned previously, there is an issue with data-
mining where searching among a range of competing rules is likely to result in at least a
couple of rules generating signiﬁcant results. In this paper, we examine in total 14,919 rules

                                                              123


---

212                                 Annals of Operations Research (2021) 297:191–220

Table 8 The percentage of rules that remain signiﬁcant at the 5% level once various multiple hypothesis
testing procedures are implemented

          Bonferroni (%)  Holm (%)  BH (%)  BY (%)  None (%)

CoinDesk  33.61           33.61     50.41   33.61   57.65
Bitstamp  27.11           27.13     46.28   28.56   58.64
Litecoin  23.26           23.26     31.84   23.26   53.23
Ripple    20.35           20.35     27.96   20.35   27.96
Ethereum  23.37           23.37     32.68   23.37   32.68

“Bonferroni” refers to the Bonferroni adjustment, while “Holm” refers to the Holm adjustment. “BH” refers
to the Benjamini and Hochberg (1995) adjustment while “BY” refers to the Benjamini and Yekutieli (2001)
adjustment. “None” refers to the percentage of rules that are signiﬁcant at the 5% level after the stationary
bootstrapping procedure of Politis and Romano (1994) is implemented

and therefore the probability of incorrectly rejecting the null hypothesis is quite high. To
circumvent this issue, we adopt a number of different procedures where we ﬁrst calculate each
rule’s individual bootstrapped p-value, which involves employing the stationary bootstrap
of Politis and Romano (1994) to resample the returns of each strategy and the individual
p-values are generated by comparing the original p-value with the bootstrapped p-values.
Table 8 presents the percentage of individual bootstrapped p-value returns are signiﬁcant
at the 5% level after the Bonferroni, Holm, BH, BY and no adjustment. The Bonferroni
adjustment is the most restrictive of all the multiple hypothesis testing procedures where
for each cryptocurrency, it suggests the lowest number of rules generate signiﬁcant returns.
However we can see that for each cryptocurrency, a large proportion of rules are signiﬁcant
even after accounting for multiple hypothesis testing. For instance, 33.61% of rules are still
statistically signiﬁcant after the Bonferroni and Hold adjustments for CoinDesk indicating
that over a third of the rules generate signiﬁcant returns. Although this ia a sharp decline
coompared to the number of signiﬁcant rules reported in Table 4, it clearly shows that technical
rules are proﬁtable in the cryptocurrency markets.

6.5 Out-of-sample performance

Another solution to address the data-snooping issue is to employ an out-of-sample analysis to
examine if the best technical trading rules from the in-sample estimation performs well out of
sample (Sullivan et al. 1999; Harvey et al. 2016). However one of the issues when examining
the out-of-sample performance of any investment strategy is the choice of the in- and out-of-
sample periods. This is especially important for technical trading rules since there is a trend
in the literature for the performance of the rules to diminish over time (Menkhoff 2007).
Further, McLean and Pontiff (2016) show that the performance for predictability variables
substantially diminish after publication in the academic literature. Also, an out-of-sample
estimation is very important with the respect of cryptocurrencies. Their volatility has been
extremely high, which has put off a number of institutions and investors from including them
in their portfolios. Further, there was a huge surge in the price of cryptocurrencies in the
second half of 2017, but especially Bitcoin where the price brieﬂy hit $20,000. The ﬁrst draft
of this paper employed data up to 31st December 2017, but since then, there has been a huge
drop in the value of cryptocurrencies, with the price hovering around $6500 in early July
2018. therefore we can offer a pure out-of-sample analysis to determine whether technical

123


---

Annals of Operations Research (2021) 297:191–220                                                          213

Table 9 This table reports the out-of-sample results for the best rule in the in-sample period

          Best rule                               Ann.Return  Ann.Sharpe                        Ann.Sortino

CoinDesk  CB2: 25/0.05/0.025/5                    − 0.0010    − 0.0502                          − 0.3470
Bitstamp  CB2: 25/0.05/0.025/3                    − 0.0091    − 0.0641                          − 0.0553
Litecoin  CB2: 25/0.05/0.025/5
Ripple    MA1: 2/0.001/1                            0.0775      1.3553                            2.1900
Ethereum  MA4: 2/25/0/1/5                           0.0546      0.7380                            1.2162
                                                    0.0631      1.1900                            1.8500

We report the best rule in the in-sample period for each cryptocurrency and then report the performance of
that rule in the out-of-sample period. Specially, we report the annualized return, annualized Sharpe ratio and
the annualized Sortino ratio. The coding for the best in-sample rules correspond to the description of the rules
in the “Appendix”

analysis in cryptocurrencies does offer predictive power as well as examine how they have
performed during the cryptocurrency bear market of the ﬁrst half of 2018.

   We provide a glimpse of the performance investors could have obtained over a pure
out-of-sample period and during the downturn in the cryptocurrency markets. Specially,
we examine the performance of the best performing rules up to 31st December 2017 and
examine how they perform during the ﬁrst 6 months of 2018, where the results are reported
in Table 9. The channel breakout rule produces the best performing rules (all very similar
in terms of parameters) for both Bitcoin prices, and Litecoin for the in-sample period, while
moving average rules are the best performing in-sample technical trading rules for Ripple and
Ethereum. In the out-of-sample periods, we ﬁnd negative annualized returns, Sharpe ratios
and Sortino ratios for both Bitcoin prices. However, the three other cryptocurrencies show
positive out-of-sample returns, as well as positive Sharpe and Sortino ratios. This indicates
that Bitcoin may not be proﬁtable to trade using technical analysis in an out-of-sample setting,
while the other cryptocurrencies we study, still generate substantial returns as well as quite
large Sharpe and Sortino ratios in the out-of-sample period.

   Bitcoin may be the least proﬁtable cryptocurrency in the out-of-sample setting Bitcoin was
the ﬁrst cryptocurrency created as well as the most liquid and therefore attracts more attention
from investors. The relatively large number of investors investors that are attracted to Bitcoin
means that proﬁtable trading strategies may be more difﬁcult to ﬁnd as the market becomes
more efﬁcient. This is also reﬂected in the academic literature where Corbet et al. (2019)
show that the majority of academic papers on cryptocurrencies solely focus on Bitcoin. Also,
the other cryptocurrencies we study are less liquid and therefore have attracted less attention
from investors suggesting that they may offer more proﬁt-making opportunities than Bitcoin.

7 Conclusion

Technical analysis has a long and rich history in the academic literature, with many papers
reporting signiﬁcant proﬁtability in foreign exchange markets, stock markets, stocks and
commodities. Although the reported proﬁtability of technical trading has declined over time,
there is still strong evidence that investors pay attention to technical trading rules and imple-
ment them as part of their investment strategies. We provide a comprehensive study on the
beneﬁt of employing a wide-range of technical trading rules in cryptocurrency markets.
Therefore we provide a large-scale investigation of the proﬁtability of technical trading rules
across ﬁve of the most liquid and proﬁtable cryptocurrencies by employing a large number of

                                                              123


---

214  Annals of Operations Research (2021) 297:191–220

technical trading rules. Furthermore, we also employ a number of multiple hypothesis tests
to safeguard against data-snooping bias.

   We employ ﬁve families of technical trading rules (consistent with Hsu et al. 2016) in
all ﬁve cryptocurrency markets and ﬁnd that technical trading rules have strong predictive
power. The annualized average return for each family of rule in each cryptocurrency market
are all statistically signiﬁcant at the 5% level indicating the robustness of the results. The
Sharpe, Sortino and Calmar ratios are also high, indicating the high risk-adjusted returns
from implementing technical trading rules in the cryptocurrency sphere. We also report the
breakeven transaction costs which generally show a value that is higher than commonly seen in
cryptocurrencies indicating that the proﬁts generated from technical trading are not wiped out
by the inclusion of transaction costs. We also show that employing technical trading rules in
cryptocurrencies generates much more favorable risk-adjusted measures than the simple buy-
and-hold strategy, and can protect investors from the large, severe and lengthly drawdowns
associated with cryptocurrencies. Finally, we implement four popular adjustments of multiple
hypothesis testing to safeguard against data-snooping bias and ﬁnd that a large proportion
of rules are still statistically signiﬁcant, ranging from 20.35% of total rules to a high of
50.41%. Finally, we show that technical trading rules cannot generate positive returns in the
out-of-sample period for Bitcoin, but can for other cryptocurrencies. Therefore our results
demonstrate that technical trading rules have signiﬁcant predictive power in cryptocurrency
markets even after accounting for multiple hypothesis testing, but Bitcoin does not offer any
predictability in the out-of-sample period.

   In this paper, we use both the Bitstamp Bitcoin price as well as the Coindesk Bitcoin
price, which is the average across Bitcoin exchanges that meet a certain criteria speciﬁed by
Coindesk. We do ﬁnd technical trading rules performance is slightly better for Coindesk than
for Bitstamp, although this difference is minimal. This difference could be due to the fact that
Coindesk is the average across numerous exchanges and is intended to serve as a standard
retail price reference for industry participants and accounting professionals. Therefore it is
a hypothetical price across exchanges for Bitcoin and may offer more inefﬁciencies that the
actual price of Bitcoin provided by Bitstamp.

   Our paper ﬁts into the literature supporting the implementation of technical trading rules
where there are numerous studies suggesting that technical trading rules are proﬁtable in
ﬁnancial markets. For instance, Hsu et al. (2016) shows that technical trading is successful
in foreign exchange markets over the long run which is supported by the ﬁndings of Zarrabi
et al. (2017), while Psaradellis et al. (2019) shows the success of technical trading rules in
the oil market. We also add to the literature on the trading opportunities that are present in
cryptocurrencies where Platanakis and Urquhart (2019) as well as Kajtazi and Moro (2019)
show that the inclusion of Bitcoin can substantially improve the risk-adjusted returns of a
stock-bond portfolio. Our ﬁndings support the ﬁndings of Detzel et al. (2018) who show
that for Bitcoin trading strategies based on moving average ratios generate economically
signiﬁcant alphas and Sharpe ratio gains relative to a buy-and-hold strategy. While the Detzel
et al. (2018) paper studies Bitcoin, we provide a wider study examining ﬁve of the largest
and most liquid cryptocurrencies and therefore will be of interest to technical traders and
cryptocurrency enthusiasts alike. We also investigate a wider range of technical trading rules
than the moving average rules used in the Detzel et al. (2018) paper.

Open Access This article is distributed under the terms of the Creative Commons Attribution 4.0 International
License (http://creativecommons.org/licenses/by/4.0/), which permits unrestricted use, distribution, and repro-
duction in any medium, provided you give appropriate credit to the original author(s) and the source, provide
a link to the Creative Commons license, and indicate if changes were made.

123


---

Annals of Operations Research (2021) 297:191–220                   215

Appendix

This appendix reports further details on the technical trading rules employed in this study,
as well as the parameters of each rule where we broadly follow the class of technical trading
rules examined by Hsu et al. (2016)

1. Moving Average Trading Rules
   Moving average trading rules are among the most widely used technical trading rules by
   traders (Taylor and Allen 1992) and they attempt to ride trends and identify imminent
   breaks in the trend or the emergence of new trends. For example, the most basic moving
   average rule is if the current price is larger (smaller) than the average of some number
   of previous prices, a buy (sell) signal is generated. However traders often replace the
   current price with a short-term moving average, or state the short-term moving average
   must be greater than the long-term moving average by a certain percentage, or persist for
   a certain number of days. We deﬁne a simple moving average as:

          M At ( j)                               =  1  j −1       (9)
                                                     j
                                                            st −i

                                                        i =0

We study ﬁve different moving average rules, namely:
MA1: If the Bitcoin price moves up as least x above M At (q) and remains so for d
periods, go long until its price moves down at least x percent below M At (q) and remains
so for d periods, at which time go short. If the price moves down at least x percent below
M At (q) and remains so for d periods, go short until the price moves up at least x above
M At (q) and remains so for d periods, at which time we go long in the currency.
MA2: If the Bitcoin price moves up as least x above M At (q) and remains so for d days,
go long for k periods and then neutralize the positions. If the price moves down at least x
percent below M At (q) and remains of or d days, go short for k days and then neutralize
the position.
MA3: If M At ( p) moves up at least x percent above M At (q) and remains so for d periods,
go long until M At ( p) moves down at least x percent below M At (q) and remains so for d
periods, at which time go short. If M At ( p) moves down at least x percent below M At (q)
and remains so for d periods, go short until M At ( p) moves up at least x percent above
M At (q) and remains so for d periods, at which time go long. p is less than q.
MA4: If M At ( p) moves up at least x percent above M At (q) and remains so for d periods,
go long for k periods, and then neutralize the position. If M At ( p) moves down at least
x percent below M At (q) and remains so for d periods, go short for k periods and then
neutralize the position. p is less than q.
MA5: If the price moves up at least x percent above any two of M At (n), M At ( p) and
M At (q) and remains so for d periods, go long with one third of the risk budget. If the
price moves up at least x percent above all three of M At (n), M At ( p) and M At (q) and
remains so for d periods, go long with all of the risk budget. If the price moves down
at least x percent below any two of M At (n), M At ( p) and M At (q) and remains so for
d periods, go short with one third of the risk budget. If the price moves down at least x
percent below all three of M At (n), M At ( p) and M At (q) and remains so for d periods,
go short with the whole risk budget. n is less than p, which is less than q.

We consider a number of different parameter speciﬁcations, namely:
q ∈ {2, 5, 10, 15, 20, 25, 50, 100, 200}, #q = 9
p ∈ {2, 5, 10, 15, 20, 25, 50, 100, 200}, # p = 9
n ∈ {2, 5, 10, 15, 20, 25, 50, 100, 200}, #n = 9

                                                                   123


---

216  Annals of Operations Research (2021) 297:191–220

    x ∈ {0, 0.01, 0.05, 0.1, 0.5, 1, 5}, #x = 7
    d ∈ {1, 2, 3, 4, 5}, #d = 5
    k ∈ {3, 5}, #k = 2
    Therefore, we study the following number of parameterizations per rule:
    M A1 = #q × #x × #d = 9 × 7 × 5 = 315
    M A2 = #q × #x × #d × #k = 9 × 7 × 5 × 2 = 945
    M A3 = #( p − q) × #x × #d = 36 × 7 × 5 = 1260
    M A4 = #( p − q) × #x × #d × #k = 36 × 7 × 5 × 2 = 2520
    M A5 = #(n − p − q) × #x × #d = 84 × 7 × 5 = 2940
    Therefore the total M A rules studied is 7980.
2. Filter Trading Rules
    The ﬁlter rule is one of the ﬁrst and simplest technical trading rules and follows the basic
    premise that investors should buy an asset when its price has risen by more than a given
    percentage above its most recent low, or sell it when the price falls by more than a given
    percentage below its most recent high. We study three different ﬁlter rules, namely:
    F1: If the Bitcoin price moves up at least x percent above its most recent low and remain
    so for d periods, go long. If the Bitcoin price moves down below its most recent high by
    at least x percent and remains so for d periods, go short. We deﬁne the most recent high
    (low) as the most recent closing price that is greater (less) than the j previous prices, for
    a given value of j.
    F2: If the Bitcoin price moves up at least x percent above its most recent low and remains
    so for d days, go long for k periods and then neutralize the position. If the price moves
    down at least x percent below its most recent high and remains so for d periods, go short
    for k periods and then neutralize the position.
    We consider a number of different parameter speciﬁcations, namely:
    x ∈ {0, 0.01, 0.05, 0.1, 0.5, 1, 5}, #x = 7
    d ∈ {1, 2, 3, 4, 5}, #d = 5
     j ∈ {2, 5, 10, 15, 20, 25, 50, 100, 200}, # j = 9
    k ∈ {3, 5}, #k = 2
    Therefore, we study the following number of parameterizations per rule:
    F1 = #x × #d × # j = 7 × 5 × 9 = 315
    F2 = #x × #d × #k × # j = 7 × 5 × 2 × 9 = 648
    Therefore the total F rules studied is 963.
3. Support-Resistance Trading Rules
    Support-resistance trading rules generate levels in which the price appears to ﬁnd difﬁ-
    culty rising beyond (resistance) or difﬁculty in penetrating (support). The main idea is
    that a break of either the resistance or support levels will indicate a further movement in
    the same direction. Therefore they are quite similar to ﬁlter rules except a signal is gener-
    ated when the price moves beyond a support or resistance level by a certain percentage,
    rather than beyond a recent high or low. We deﬁne a resistance level as the highest price
    of the j previous prices and we deﬁne a support level as the lowest closing rates of j
    previous closing and the two rules we examine are:
    SR1: If the price moves up at least x percent above the highest closing of the j previous
    price and remains so for d periods, go long. If the price moves down at least x percent
    below the lowest closing of the previous j prices and remains so for d days, go short.
    SR2: If the price moves up at least x percent above the highest price of the j previous
    prices and remains so for d days, go long for k days and then neutralize the position. If
    the price moves down at least x percent below the lowest price of the j previous closing
    rates and remains so for d days, go short for k days and then neutralize the position.

123


---

Annals of Operations Research (2021) 297:191–220                   217

   We consider a number of different parameter speciﬁcations, namely:
   x ∈ {0, 0.01, 0.05, 0.1, 0.5, 1, 5}, #x = 7
   d ∈ {1, 2, 3, 4, 5}, #d = 5
    j ∈ {2, 5, 10, 15, 20, 25, 50, 100, 200}, # j = 9
   k ∈ {3, 5}, #k = 5
   Therefore, we study the following number of parameterizations per rule:
   S R1 = #x × #d × # j = 7 × 5 × 9 = 315
   S R2 = #x × #d × # j × #k = 7 × 5 × 9 × 2 = 630
   Therefore the total S R rules studied is 945.
4. Oscillator Trading Rules
   A popular type of technical trading rule employed in the foreign exchange market is over-
   bought/oversold indicator, which aims to indicate that the price movement in a particular
   direction has been too rapid and that a correction is imminent. One of the most popular
   oscillator rules is the relative strength indicator (R S I ) which is:

R S It (h) = 100                                       Ut (h)      (10)
                                                  Ut (h) + Dt (h)

   where Ut (h) denotes the cumulated up movement of prices over the previous h periods,
   and Dt (h) denotes the cumulative absolute downward movement over the previous h
   periods. Therefore the R S I indicator measures the strength of upward movements relative
   to downward movements and is normalized to lie between 0 and 100. We examine two
    R S I rules, namely:
   O1: If R S It (h) moves above 50 + v for at least d periods and then subsequently moves
   below 50 + v, go short. If R S It (h) moves below 50 − v for at least d periods and then
   subsequently moves above 50 − v, go long.
   O2: If R S It (h) moves above 50 + v for at least d periods and then subsequently moves
   below 50 + v, go short for k periods and then neutralize the position. If R S It (h) moves
   below 50 − v for at least d periods and then subsequently moves above 50 − v, go long
   for k periods and then neutralize the position.
   We consider a number of different parameter speciﬁcations, namely:
   h ∈ {2, 5, 10, 15, 20, 25, 50, 100, 200}, #h = 9
   v ∈ {2, 5, 10, 15, 20, 25}, #v = 6
   d ∈ {1, 2, 3, 4, 5}, #d = 4
   k ∈ {2, 5}, #k = 2
   Therefore, we study the following number of parameterizations per rule:
    O1 = #h × #v × #d = 9 × 6 × 5 = 270
    O2 = #h × #v × #d × #k = 9 × 6 × 5 × 2 = 540
   Therefore the total O rules studied is 810.
5. Channel Breakout Trading Rules
   A channel breakout trading rule generates a channel around the price when the highest
   price over a previous given period is within a given range of the lowest level over the
   previous given period so that, there are time-varying support and resistance levels that
   appear to be drifting together within a certain range. A trading signal is therefore generated
   when the price penetrates beyond the upper or lower bond of the channel since the rule
   suggests that once a channel is breached, there will be sustained movement in the same
   direction. A c% trading channel is deﬁned as occurring when the high level of the price
   over the previous j periods is within c% of the low over the previous j periods so that
   there are time-varying support and resistance levels that appear to be drifting together
   with about c% or less separation. These time-varying support and resistance levels are

                                                                   123


---

218  Annals of Operations Research (2021) 297:191–220

     the lower and upper bonds where the upper bound at a particular period will be c% above
     the low of the previous j periods and the lower bound will be c% below the high of the
     previous j periods. We examine two channel breakout rules, namely:
     CB1: If a c% trading channel exists and if the price moves up at least x percent above
     the upper bound of the channel and remains so for d periods, go long. If a c% trading
     channel exists and if the price moves down at least x percent below the lower bound of
     the channel and remains so for d periods, go short.
     CB2: CB1: If a c% trading channel exists and if the price moves up at least x percent
     above the upper bound of the channel and remains so for d periods, go long for k periods
     and then neutralize the position. If a c% trading channel exists and if the price moves
     down at least x percent below the lower bound of the channel and remains so for d
     periods, go short for k periods and then neutralize the position
     We consider a number of different parameter speciﬁcations, namely:
     x ∈ {0, 0.01, 0.05, 0.1, 0.5, 1, 5}, #x = 7
     d ∈ {2, 3, 4, 5}, #d = 4
     j ∈ {2, 5, 10, 25, 50, 75, 100, 150, 200}, # j = 9
     c ∈ {0.05, 0.01, 0.5, 0.1, 0.25, 0.5}, #c = 6
     k ∈ {3, 5}, #k = 2
     Therefore, we study the following number of parameterizations per rule:
     C B1 = #x × #d × # j × #c = 7 × 4 × 9 × 6 = 1512
     C B2 = #x × #d × # j × #c × #k = 7 × 4 × 9 × 6 × 2 = 3024
     Therefore the total C B rules studied is 4536.
     The total number of different technical trading considered are: 7980 + 963 + 630 + 810
     + 4536 = 14,919.

References

Allen, F., & Karjalainen, R. (1999). Using genetic algorithms to ﬁnd technical trading rules. Journal of
      Financial Economics, 51, 245–271.

Bajgrowicz, P., & Scaillet, O. (2012). Technical trading revisited: False discoveries, persistence tests, and
      transaction costs. Journal of Financial Economics, 106, 473–491.

Bariviera, A. F. (2017). The inefﬁciency of bitcoin revisited: A dynamic approach. Economics Letters, 161,
      1–4.

Batten, J. A., Lucey, B. M., McGroarty, F., Peat, M., & Urquhart, A. (2018). Does intraday technical trading
      have predictive power in precious metal markets? Journal of International Financial Markets, Institutions
      and Money, 52, 102–113.

Baur, D. G., Hong, K., & Lee, A. D. (2018). Bitcoin: Medium of exchange or speculative assets? Journal of
      International Financial Markets, Institutions and Money, 54, 177–189.

Benjamini, Y., & Hochberg, Y. (1995). Controlling the false discovery rate: A practical and powerful approach
      to multiple testing. Journal of the Royal Statistical Society, Series B, 57, 289–300.

Benjamini, Y., & Yekutieli, D. (2001). The control of the false discovery rate in multiple testing under depen-
      dency. Annals of Statistics, 29, 1165–1188.

Bessembinder, H., & Chan, K. (1998). Market efﬁciency and the returns to technical analysis. Financial
      Management, 27, 5–17.

Bouri, E., Molnár, P., Azzic, G., Roubaud, D., & Lars Hagfors, I. H. (2017). On the hedge and safe haven
      properties of bitcoin: Is it really more than a diversiﬁer? Finance Research Letters, 20, 192–198.

Brandvold, M., Molnár, P., Vagstad, K., & Valstad, O. C. A. (2015). Price discovery on bitcoin exchanges.
      Journal of International Financial Markets, Institutions and Money, 36, 18–35.

Brauneis, A., & Mestel, R. (2018). Price discovery of cryptocurrencies: Bitcoin and beyond. Economics Letters,
      165, 58–61.

Brière, M., Oosterlinck, K., & Szafarz, A. (2015). Virtual currency, tangible return: Portfolio diversiﬁcation
      with bitcoin. Journal of Asset Management, 16, 365–373.

123


---

Annals of Operations Research (2021) 297:191–220  219

Brock, W., Lakonishok, J., & LeBaron, B. (1992). Simple technical trading rules and the stochastic properties
      of stock returns. Journal of Finance, 47, 1731–1764.

Cheah, E. T., & Fry, J. (2015). Speculative bubbles in bitcoin markets? an empirical investigation into the
      fundamental value of bitcoin. Economics Letters, 130, 32–36.

Chordia, T., Goyal, A., & Saretto, A. (2018). p-hacking. SSRN Available at: https://ssrn.com/
      abstract=3017677 (pp. 32–36).

Ciaian, P., Rajcaniova, M., & Kancs, D. (2018). Virtual relationships: Short- and long-run evidence from
      bitcoin and altcoin markets. Journal of International Financial Markets, Institutions and Money, 52,
      173–195.

Corbet, S., Lucey, B., Urquhart, A., & Yarovaya, L. (2019). Cryptocurrencies as a ﬁnancial asset: A systematic
      analysis. International Review of Financial Analysis, 62, 182–199.

Corbet, S., Lucey, B., & Yarovaya, L. (2018). Datestamping the bitcoin and ethereum bubbles. Finance
      Research Letters, 26, 81–88.

Corbet, S., Meegan, A., Larkin, C., Lucey, B., & Yarovaya, L. (2018). Exploring the dynamic relationships
      between cryptocurrencies and other ﬁnancial assets. Economics Letters, 165, 28–34.

Detzel, A. L., Liu, H., Strauss, J., Zhou, G., & Zhu, Y. (2018). Bitcoin: Learning, predictability and proﬁtability
      via technical analysis. Available at SSRN: https://ssrn.com/abstract=3115846.

Dyhrberg, A. H. (2016a). Bitcoin, gold and the dollar—A GARCH volatility analysis. Finance Research
      Letters, 16, 85–92.

Dyhrberg, A. H. (2016b). Hedging capabilities of bitcoin. Is it the virtual gold? Finance Research Letters, 16,
      139–144.

Fry, J., & Cheah, E. T. (2016). Negative bubbles and shocks in cryptocurrency markets. International Review
      of Financial Analysis, 47, 343–352.

Gencay, R. (1999). Linear, non-linear and essential foreign exchange rate prediction with simple technical
      trading rules. Journal of International Economics, 47, 91–107.

Han, Y., Hu, T., & Yang, K. (2016). Are there exploitable trends in commodity futures prices? Journal of
      Banking and Finance, 70, 214–234.

Han, Y., Yang, K., & Zhou, G. (2013). A new anomaly: The cross-sectional proﬁtability of technical analysis.
      Journal of Financial and Quantitative Analysis, 48, 1433–1461.

Harvey, C., Liu, Y., & Zhu, H. (2016).... and the cross-section of expected returns. Review of Financial Studies,
      29, 5–68.

Harvey, C. R., & Liu, Y. (2014). Evaluating trading strategies. The Journal of Portfolio Management, 40,
      108–118.

Hsu, P.-H., Taylor, M. P., & Wang, Z. (2016). Technical trading: Is it still beating the foreign exchange market?
      Journal of International Economics, 102, 188–208.

Hudson, R., McGroarty, F., & Urquhart, A. (2017). Sampling frequency and the performance of different types
      of technical trading rules. Finance Research Letters, 22, 136–139.

Kajtazi, A., & Moro, A. (2019). The role of bitcoin in well diversiﬁed portfolios: A comparative global study.
      International Review of Financial, 61, 143–157.

Levich, R. M., & Thomas, L. R. (1993). The signiﬁcance of technical trading-rule proﬁts in the foreign
      exchange market: A bootstrap approach. Journal of International Money and Finance, 12, 451–474.

Lintilhac, P. S., & Tourin, A. (2017). Model-based pairs trading in the bitcoin markets. Quantitative Finance,
      17, 703–716.

Marshall, B. R., Cahan, R. H., & Cahan, J. M. (2008a). Can commodity futures be proﬁtably traded with
      quantitative market timing strategies? Journal of Banking and Finance, 32, 1810–1819.

Marshall, B. R., Cahan, R. H., & Cahan, J. M. (2008b). Does intraday technical analysis in the U.S. equity
      market have value? Journal of Empirical Finance, 15, 199–210.

Marshall, B. R., Nguyen, N. H., & Visaltanachoti, N. (2017). Time series momentum and moving average
      trading rules. Quantitative Finance, 17, 405–421.

McLean, R. D., & Pontiff, J. (2016). Does academic research destroy stock return predictability? The Journal
      of Finance, 71, 5–32.

Menkhoff, L. (2007). The obstinate passion of foreign exchange professionals: Technical analysis. European
      Journal of Finance, 145, 936–972.

Miffre, J., & Rallis, G. (2007). Momentum strategies in commodity futures markets. Journal of Banking and
      Finance, 31, 1863–1886.

Moskowitz, T. J., Ooi, Y. H., & Pedersen, L. H. (2012). Time series momentum. Journal of Financial Eco-
      nomics, 104, 228–250.

Nadarajah, S., & Chu, J. (2017). On the inefﬁciency of bitcoin. Economics Letters, 150, 6–9.
Nakamoto, S. (2008). Bitcoin: A peer-to-peer electronic cash system. https://Bitcoin.org/Bitcoin.pdf.

                                                  123


---

220  Annals of Operations Research (2021) 297:191–220

Narayan, P. K., Ahmed, H. A., & Narayan, S. (2015). Do momentum-based trading strategies work in the
      commodity futures markets? Journal of Futures Markets, 35, 868–891.

Neely, C. J., Rapach, D. E., Tu, J., & Zhou, G. (2014). Forecasting the equity risk premium: The role of
      technical indicators. Management Science, 60, 1772–1791.

Neely, C. J., Weller, P., & Dittmar, R. (1997). Is technical analysis in the foreign exchange market proﬁtable?
      A genetic programming approach. Journal of Financial and Quantitative Analysis, 32, 405–426.

Olson, D. (2004). Have trading rule proﬁts in the currency markets declined over time? Journal of Banking
      and Finance, 28, 485–105.

Platanakis, E., Sutcliffe, C., & Urquhart, A. (2018). Optimal vs naïve diversiﬁcation in cryptocurrencies.
      Economics Letters, 171, 93–96.

Platanakis, E., & Urquhart, A. (2019). Should investors include bitcoin in their portfolios? a portfolio theory
      approach. Available at SSRN: https://ssrn.com/abstract=3215321.

Politis, D., & Romano, J. (1994). The stationary bootstrap. Journal of the American Statistical Association,
      89, 1303–1313.

Poole, W. (1967). Speculative prices as random walks: An analysis of ten time series of ﬂexible exchange
      rates. Southern Economic Journal, 33, 468–478.

Psaradellis, I., Laws, J., Pantelous, A. A., & Sermpinis, G. (2019). Performance of technical trading rules:
      evidence from the crude oil market. European Journal of Finance, forthcoming.

Qi, M., & Wu, Y. (2006). Technical trading-rule proﬁtability, data snooping, and reality check: Evidence from
      the foreign exchange market. Journal of Money, Credit and Banking, 30, 2135–2158.

Shynkevich, A. (2012). Performance of technical analysis in growth and small cap segments of the us equity
      market. Journal of Banking and Finance, 36, 193–208.

Shynkevich, A. (2016). Predictability in bond returns using technical trading rules. Journal of Banking and
      Finance, 70, 55–69.

Smith, D. M., Wang, N., Wang, Y., & Zychowicz, E. J. (2016). Sentiment and the effectiveness of technical
      analysis: Evidence from the hedge fund industry. Journal of Financial and Quantitative Analysis, 51,
      1991–2013.

Sullivan, R., Timmermann, A., & White, H. (1999). Data-snooping, technical trading rule performance, and
      the bootstrap. Journal of Finance, 354, 1647–1691.

Sweeney, R. J. (1986). Beating the foreign exchange market. Journal of Finance, 41, 163–182.
Szakmary, A. C., Shen, Q., & Sharma, S. C. (2010). Trend-following trading strategies in commodity futures:

      A re-examination. Journal of Banking and Finance, 34, 409–426.
Taylor, M. P., & Allen, H. (1992). The use of technical analysis in the foreign exchange market. Journal of

      International Money and Finance, 11, 304–314.
Timmermann, A., & Granger, C. W. J. (2004). Efﬁcient market theory and forecasting. International Journal

      of Forecasting, 50, 15–27.
Tiwari, A. K., Jana, R. K., Das, D., & Roubaud, D. (2018). Informational efﬁciency of bitcoin-an extension.

      Economics Letters, 163, 106–109.
Urquhart, A. (2016). The inefﬁciency of Bitcoin. Economics Letters, 148, 80–82.
Urquhart, A. (2017). Price clustering in bitcoin. Economics Letters, 159, 145–148.
Urquhart, A., Gebka, B., & Hudson, R. (2015). How exactly do markets adapt? Evidence from the moving

      average rule in three developed markets. Journal of International Financial Markets, Institutions and
      Money, 38, 127–147.
Urquhart, A., & Zhang, H. (2019). Is bitcoin a hedge or safe haven for currencies? An intraday analysis.
      International Review of Financial, 64, 49–57.
White, H. (2000). A reality check for data snooping. Econometrica, 65, 1097–1126.
Yamamoto, R. (2012). Intraday technical analysis of individual stocks on the tokyo stock exchange. Journal
      of Banking and Finance, 36, 3033–3047.
Young, T. W. (1991). Calmar ratio: A smoother tool. Futures, 20(1), 40.
Young, T. W. (1991). Calmar ratio: A smoother tool. Futures, 20(1), 40.
Zarrabi, N., Snaith, S., & Coakley, J. (2017). Fx technical trading rules can be proﬁtable sometimes!. Inter-
      national Review of Financial Analysis, 49, 113–127.

Publisher’s Note Springer Nature remains neutral with regard to jurisdictional claims in published maps and
institutional afﬁliations.

123


---


