# DecisionBot

DecisionBot is a Reddit bot that retrieves and posts mixed martial arts scorecards on-demand. Users summon the bot by commenting in any [r/mma](https://www.reddit.com/r/mma) thread with the fighters' names. It has been live on r/mma since February 2017.

* [Example of use in discussion](https://www.reddit.com/r/MMA/comments/616fhz/coach_del_fierro_says_exchamp_dominick_cruz_is/dfc7ose)
* [Usage guide on Reddit](https://www.reddit.com/r/bottesting/comments/606f58/decisionbot_usage_examples/)
* [Initial release thread on r/mma](https://www.reddit.com/r/MMA/comments/5vy9cc/decisionbot_new_rmma_bot_that_posts_decision/)

## Usage example
* User leaves comment: **decisionbot mcgregor vs diaz**
* DecisionBot replies:

    ### [**CONOR MCGREGOR defeats NATE DIAZ** (*majority decision*)](http://mmadecisions.com/decision/7244/fight)

    UFC 202: Diaz vs. McGregor 2 — August 20, 2016

    ROUND|McGregor|Diaz| |McGregor|Diaz| |McGregor|Diaz
    :-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:
    1|10|9| |10|9| |10|9
    2|10|9| |10|9| |10|9
    3|9|10| |9|10| |8|10
    4|10|9| |10|9| |10|9
    5|9|10| |9|10| |9|10
    **TOTAL**|**48**|**47**| |**48**|**47**| |**47**|**47**

    *Judges, in order: Derek Cleary, Jeff Mullen, Glenn Trowbridge.*

    **MEDIA MEMBER SCORES**

    * **1/19** people scored it **49-47 McGregor**.
    * **12/19** people scored it **48-47 McGregor**.
    * **1/19** people scored it **47-46 McGregor**.
    * **4/19** people scored it **47-47 DRAW**.
    * **1/19** people scored it **47-48 Diaz**.

    Avg. media score: **47.7-47.0 McGregor** (*high certainty<sup>[[1]](https://redd.it/9p4xc7)</sup>*).

    *2215 fan scores* — *1426 (64%)* ***McGregor***, *483 (22%)* ***Diaz***, *306 (14%)* ***Draw***.

## Features
* You can use v / v. / vs / vs. / versus, or leave it out and the bot will figure the names out.
* Handles rematches (include the rematch number in the comment, or leave it out and the bot posts all fights).
* Handles many fighter nicknames and common name misspellings.
* Supports returning ["certainty of victory" confidence level](https://www.reddit.com/r/DecisionBot/comments/9p4xc7/confidence_level_explanation/) based on media scorecards.
* Banters and has many easter eggs.

## How to Run

Without Docker:
* Run `python decisionbot.py [--debug]`

With Docker:
* `make build` to build the image + create a container
* `make` to run (in background)
* `make restart` to restart (in background)

## Files
File|Description
:-:|---
*fight_finder.py*|Searches and pulls fight data from [mmadecisions.com](http://mmadecisions.com/) using [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/).
*decision_bot.py*|Runs the bot on Reddit.
*notify_account.py*|Notifies my personal account of DecisionBot's status.
*config.yaml*|Bot configs.
*commented.txt*|List of recent comment ids that triggered the bot.
*nicknames.txt*|List of common nicknames and name misspellings.
*rematches.txt*|Correctly adjusted rematch numbers (if there was a finished fight, the rematch numbers need to be adjusted).

## Praise
* *["This is one of the coolest and most useful bots I've seen on Reddit. True story."](https://www.reddit.com/r/MMA/comments/6656t9/this_legend_returns_saturday/dgfyzqz/?context=3)*
* *["wtf im speechless , this is amazing! what a time to be alive"](https://www.reddit.com/r/MMA/comments/6656t9/this_legend_returns_saturday/dgg06i6/?context=10000)*
* *["ALL GLORY TO THE BOT"](https://www.reddit.com/r/MMA/comments/636xw6/video_gsp_dominates_jon_fitch_for_5_rounds_in_one/dfs9tnq/?context=10000)*
* *[".... you just summoned a decision bot...?... the internet truly is wondrous."](https://www.reddit.com/r/MMA/comments/63ars2/aldo_vs_holloway_ufc_212/dfsu96p/?context=10000)*
* *["wow! very fantastic bot!"](https://www.reddit.com/r/MMA/comments/61rwx9/al_iaquinta_happy_to_be_past_contract/dfgu15j/?context=3)*
* *["I did not even know this magic existed."](https://www.reddit.com/r/MMA/comments/5yrbbo/official_general_discussion_thread_march_11_2017/desorq1/?context=3)*
* *["What is this voodoo?"](https://www.reddit.com/r/MMA/comments/5xl567/official_ufc_209_woodley_vs_thompson_2_live/deixg9v/?context=10000)*
* *["Decisionbot I love you man."](https://www.reddit.com/r/MMA/comments/5xcqnu/nate_diaz_was_considered_as_a_late_replacement_to/deh4azr/?context=3)*
* *["God I love this bot."](https://www.reddit.com/r/MMA/comments/5x1lk6/official_general_discussion_thread_march_02_2017/deflghh/?context=3)*
