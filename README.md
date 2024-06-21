### replit-platformer
Simple platformer made using replit-play
- Levels are stored as CSV files
- each cell in the spreadsheet represents a "box", the type of which is determined by its integer value
  - e.g. air=0, dirt=1, ...
  - Easiest way to design levels is to use a spreadsheet program (e.g. google sheets) then exporting to CSV
- As the player moves, platforms ahead are loaded so they appear continuous and platforms behind are unloaded


Demo of how it works:

![video of demo](https://github.com/winston-de/replit_platformer/blob/main/demo.gif?raw=true)