# tutorial-swap-bot

## How to run
For the telegram module, run `pip3 install python-telegram-bot==13.7`. All other modules are installed with default version. Simply run the code in the same folder as the json file.

## Inspiration
We recently saw a group of 5 people trying to figure out how to swap their tutorial slots to get everyone their preferred tutorial slots and realised that there could be many such possible circular swaps that many students do not see. We decided to make a telegram bot to aid this situation and help more students get their preferred tutorial slots.

## What it does
Students can key in their current slot and the slot they want. When a possible swap is found, an image with how to carry out the swap will be sent to all involved users with the telegram handles of all the involved users for them to discuss.

## How we built it
We used a python telegram bot API to code the functionality of the telegram bot. We coded a cycle detection algorithm to detect if there were any cycles in the slots to be swapped. When a cycle is detected, the bot will create an image displaying the cycle and all involved personnel's telegram handles for them to discuss.

We also used NUSMods API to fetch a list of modules for error checking and to provide a menu for ease of users to provide their answers. 

## Challenges we ran into
It was the first time for us coding a telegram bot so a lot of the API was new to us. It was also difficult coding the cycle detection algorithm for this case.

## Accomplishments that we're proud of
Making a working product for our first time building a telegram bot

## What we learned
How to use the telegram bot APIs

## What's next for Tutorial Swap Bot
Adding asynchronization for multiple users to use the bot at the same time. Improving the cycle detection algorithm.
