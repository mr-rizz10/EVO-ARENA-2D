# 🎮 EVO ARENA 2D

So this started as a uni AI Lab assignment and kind of turned into our favorite project of the trimester. EvoArena is a top-down 2D shooter where the enemies actually pay attention to how you play — and change their tactics because of it.

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)
![Pygame](https://img.shields.io/badge/Pygame-2.6-green?logo=pygame&logoColor=white)
![Status](https://img.shields.io/badge/status-complete-success)

We were very much beginners going in, so don't expect anything fancy under the hood — no neural nets, no reinforcement learning, none of that. Just three solid, explainable AI techniques doing real work together. We can actually explain every line of this to our professor without hand-waving, which was kind of the whole point.

---

## What's actually going on here

The pitch is simple: play a level, the AI watches what you do, figures out if you're the type to run in guns blazing or hang back and snipe, and then changes how the enemies behave next level because of it. It does this for 3 levels, then stops "learning" and just uses whatever it figured out for a final battle.

We used three techniques to pull this off:

- **A Finite State Machine** for every enemy (PATROL, CHASE, ATTACK, RETREAT) — this is the stuff that was in our DSA coursework honestly, just applied to a game instead of a textbook problem.
- **A\* pathfinding** so enemies actually walk around the walls we put in the arena instead of just ramming into them like idiots.
- **Rule-based scoring** to figure out your playstyle — we track how much you move, how often you shoot, how close you get to enemies, and run it all through some weighted formulas we wrote ourselves. No ML libraries, just math we could explain line by line.

Depending on what you're classified as, enemies pick one of three strategies:

```
you play AGGRESSIVE  ->  enemies SURROUND you
you play DEFENSIVE    ->  enemies RUSH you
you play RANGED        ->  enemies KEEP THEIR DISTANCE
```

We genuinely debated the mapping for a while (should aggressive players get rushed or surrounded?) and landed on surrounding being the "punish" response to an aggressive player since it's the one that actually counters charging in.

---

## Controls

- `WASD` to move
- `SPACE` or left click to shoot (aims at your mouse)
- `ENTER` to move through menus / level transitions
- `F1` if you want to see the debug overlay (shows what state each enemy is in and the current strategy — genuinely useful for showing off what's happening under the hood)
- `ESC` to quit

---

## Running it yourself

Fair warning — getting pygame installed gave us more trouble than the actual AI code did. If you're on a brand new Python version (3.13/3.14), pygame doesn't have a pre-built package yet and pip will try to compile it from source, which fails with a `distutils`-related error. Save yourself the headache and just use **Python 3.12**.

```bash
git clone https://github.com/mr-rizz10/EVO-ARENA-2D.git
cd EVO-ARENA-2D
pip install pygame
python main.py
```

If `pip install pygame` tries to build from source instead of just grabbing a wheel file, that's your sign you're on too new a Python version — go grab 3.12 and try again.

---

## How the files are laid out

```
EvoArena/
├── main.py          # the thing you actually run
├── settings.py      # every number/color we tweaked lives here
├── game.py          # the big one — runs the game loop, states, HUD
├── player.py        # you, basically
├── enemy.py         # the FSM + pathfinding brain for enemies
├── ai.py            # the actual "learning" logic
├── pathfinding.py   # A* search, no game-specific stuff in here
├── bullet.py        # shared projectile class
└── README.md
```

We kept `ai.py` completely free of any pygame code on purpose — it just takes in numbers and spits out a decision. Means we could test the whole scoring system separately before we even had it hooked up to the actual game, which saved us a lot of debugging time later.

---

## A playthrough looks like this

```
Level 1 -> AI watches you -> figures out your type -> picks a strategy
Level 2 -> enemies use it -> AI watches again -> adjusts
Level 3 -> last adjustment -> learning turns off for good
Final Battle -> enemies stick with whatever they learned
Dashboard -> shows your stats, final strategy, and how it all evolved
```

After each level there's a quick analysis screen so you can actually see what the AI decided and why — we wanted this to be something we could point at during the demo and say "see, this number went up, so the strategy changed to this," rather than just trusting us that something smart is happening behind the curtain.

---

## Built with

Just Python and Pygame. That's genuinely it — no external assets, no API keys, nothing that needs internet access once it's running. Everything you see is basic shapes drawn directly by pygame.

---

## A note on scope

We left stuff like Q-Learning and neural networks out on purpose, not because we didn't know they existed but because the whole point was building something we could actually finish, debug, and explain confidently as beginners. `ai.py` is structured so something fancier could slot in later if we ever wanted to revisit this.
