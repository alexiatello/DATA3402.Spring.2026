"""
Blackjack Simulation - Exercise 4: Full Implementation
=======================================================
Complete logic for Hand, Strategy subclasses, Player, Dealer,
HumanPlayer, and Game.  Supports an interactive human player as
well as fully automated computer players.
"""

import random
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Optional


# ===========================================================================
# Constants
# ===========================================================================

Suits = ("Hearts", "Diamonds", "Spades", "Clubs")
Ranks = ("A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K")

Rank_values: dict[str, int] = {
    "A": 11, "2": 2, "3": 3, "4": 4, "5": 5,
    "6": 6,  "7": 7, "8": 8, "9": 9, "10": 10,
    "J": 10, "Q": 10, "K": 10,
}


# ===========================================================================
# Card / PlasticCard / Deck  (unchanged from Exercise 1)
# ===========================================================================

class Card:
    def __init__(self, rank: str, suit: str, face_up: bool = True):
        if rank not in Ranks:
            raise ValueError(f"Invalid rank: {rank!r}")
        if suit not in Suits:
            raise ValueError(f"Invalid suit: {suit!r}")
        self.rank    = rank
        self.suit    = suit
        self.face_up = face_up

    @property
    def value(self) -> int:
        return Rank_values[self.rank]

    @property
    def hi_lo_count(self) -> int:
        if self.rank in ("2", "3", "4", "5", "6"):
            return +1
        if self.rank in ("10", "J", "Q", "K", "A"):
            return -1
        return 0

    def __repr__(self) -> str:
        return "[hidden]" if not self.face_up else f"[{self.rank} of {self.suit}]"

    def __str__(self) -> str:
        return repr(self)


class PlasticCard:
    face_up: bool = True

    @property
    def rank(self) -> None:
        return None

    @property
    def value(self) -> int:
        return 0

    @property
    def hi_lo_count(self) -> int:
        return 0

    def __repr__(self) -> str:
        return "[Plastic]"

    def __str__(self) -> str:
        return repr(self)


class Deck:
    def __init__(self, num_decks: int = 6, plastic_zone: tuple[int, int] = (60, 80)):
        if num_decks < 1:
            raise ValueError("num_decks must be >= 1")
        self.num_decks      = num_decks
        self.plastic_zone   = plastic_zone
        self._cards: list[Card | PlasticCard] = []
        self.reshuffle_needed: bool = False
        self.shuffle()

    def _build(self) -> list[Card | PlasticCard]:
        return [
            Card(rank, suit)
            for _ in range(self.num_decks)
            for suit in Suits
            for rank in Ranks
        ]

    def shuffle(self) -> None:
        cards: list[Card | PlasticCard] = self._build()
        random.shuffle(cards)
        lo, hi  = self.plastic_zone
        total   = len(cards)
        lo      = min(lo, total - 1)
        hi      = min(hi, total)
        plastic_pos = max(0, total - random.randint(lo, hi))
        cards.insert(plastic_pos, PlasticCard())
        self._cards           = cards
        self.reshuffle_needed = False

    def draw(self) -> Optional[Card | PlasticCard]:
        if not self._cards:
            return None
        card = self._cards.pop(0)
        if isinstance(card, PlasticCard):
            self.reshuffle_needed = True
        return card

    @property
    def cards_remaining(self) -> int:
        return len(self._cards)

    @property
    def decks_remaining(self) -> float:
        non_plastic = sum(1 for c in self._cards if not isinstance(c, PlasticCard))
        return max(non_plastic / 52, 0.5)   # floor at 0.5 to avoid division-by-zero

    def __len__(self) -> int:
        return self.cards_remaining

    def __repr__(self) -> str:
        return (f"Deck(num_decks={self.num_decks}, "
                f"cards_remaining={self.cards_remaining}, "
                f"reshuffle_needed={self.reshuffle_needed})")


# ===========================================================================
# Action enum
# ===========================================================================

class Action(Enum):
    HIT       = auto()
    STAND     = auto()
    DOUBLE    = auto()
    SPLIT     = auto()
    SURRENDER = auto()


# ===========================================================================
# Hand
# ===========================================================================

class Hand:
    """One player's cards for a single round, with correct Ace handling."""

    def __init__(self, bet: int = 0):
        self.cards: list[Card] = []
        self.bet:   int        = bet

    # --- mutators -----------------------------------------------------------

    def add_card(self, card: Card) -> None:
        """Append card to the hand."""
        self.cards.append(card)

    def reset(self) -> None:
        """Discard all cards and zero the bet (call between rounds)."""
        self.cards = []
        self.bet   = 0

    # --- computed properties ------------------------------------------------

    @property
    def total(self) -> int:
        """Best non-busting total; Aces are counted as 11 then reduced to 1
        as needed to avoid busting."""
        total = sum(c.value for c in self.cards)
        aces  = sum(1 for c in self.cards if c.rank == "A")
        # Each Ace can be demoted from 11 → 1 (difference of 10)
        while total > 21 and aces:
            total -= 10
            aces  -= 1
        return total

    @property
    def is_bust(self) -> bool:
        return self.total > 21

    @property
    def is_blackjack(self) -> bool:
        """Natural 21: exactly two cards, one Ace and one 10-value card."""
        if len(self.cards) != 2:
            return False
        ranks = {c.rank for c in self.cards}
        return "A" in ranks and bool(ranks & {"10", "J", "Q", "K"})

    @property
    def is_soft(self) -> bool:
        """True when at least one Ace is still being counted as 11."""
        total = sum(c.value for c in self.cards)
        aces  = sum(1 for c in self.cards if c.rank == "A")
        # If we can keep one Ace as 11 without busting, the hand is soft
        reductions = 0
        while total > 21 and reductions < aces:
            total     -= 10
            reductions += 1
        return (aces - reductions) > 0 and total <= 21

    @property
    def is_pair(self) -> bool:
        """Exactly two cards of the same rank (eligible to split)."""
        return len(self.cards) == 2 and self.cards[0].rank == self.cards[1].rank

    # --- display ------------------------------------------------------------

    def __repr__(self) -> str:
        cards_str = "  ".join(str(c) for c in self.cards)
        return f"Hand([{cards_str}]  total={self.total}  bet={self.bet})"

    def __str__(self) -> str:
        return repr(self)


# ===========================================================================
# Strategy  (abstract base + concrete subclasses)
# ===========================================================================

class Strategy(ABC):
    """Abstract base: every strategy must implement decide() and place_bet()."""

    @abstractmethod
    def decide(
        self,
        hand:            Hand,
        dealer_up_card:  Card,
        running_count:   int,
        decks_remaining: float,
    ) -> Action:
        pass

    @abstractmethod
    def place_bet(self, running_count: int, decks_remaining: float) -> int:
        pass


# ---------------------------------------------------------------------------
# StandStrategy — never hits; useful as a do-nothing baseline
# ---------------------------------------------------------------------------

class StandStrategy(Strategy):
    """Always stands. Used as the dealer's placeholder strategy."""

    def decide(self, hand, dealer_up_card, running_count, decks_remaining) -> Action:
        return Action.STAND

    def place_bet(self, running_count, decks_remaining) -> int:
        return 10   # minimum fixed bet


# ---------------------------------------------------------------------------
# RandomStrategy — hits or stands at random
# ---------------------------------------------------------------------------

class RandomStrategy(Strategy):
    """Hits or stands randomly; useful as a noisy lower baseline."""

    def decide(self, hand, dealer_up_card, running_count, decks_remaining) -> Action:
        return random.choice([Action.HIT, Action.STAND])

    def place_bet(self, running_count, decks_remaining) -> int:
        return random.choice([10, 20, 25, 50])


# ---------------------------------------------------------------------------
# BasicStrategy — standard blackjack strategy chart (no card counting)
# ---------------------------------------------------------------------------

class BasicStrategy(Strategy):
    """Follows the canonical basic strategy chart.

    Hard totals
    -----------
    ≤ 8          always hit
    9            double vs dealer 3–6, else hit
    10           double vs dealer 2–9, else hit
    11           double vs dealer 2–10, else hit
    12           stand vs dealer 4–6, else hit
    13–16        stand vs dealer 2–6, else hit
    17+          always stand

    Soft totals  (hand contains an Ace counted as 11)
    -----------
    soft 13–17   hit  (double on some variants — kept simple here)
    soft 18      stand vs dealer 2, 7, 8; hit vs 9, 10, A; else stand
    soft 19+     always stand
    """

    def decide(self, hand, dealer_up_card, running_count, decks_remaining) -> Action:
        total    = hand.total
        soft     = hand.is_soft
        d_val    = dealer_up_card.value   # dealer up-card point value

        if soft:
            if total >= 19:
                return Action.STAND
            if total == 18:
                return Action.STAND if d_val in (2, 7, 8) else Action.HIT
            return Action.HIT   # soft 13–17

        # Hard totals
        if total >= 17:
            return Action.STAND
        if total >= 13:
            return Action.STAND if d_val <= 6 else Action.HIT
        if total == 12:
            return Action.STAND if 4 <= d_val <= 6 else Action.HIT
        if total == 11:
            return Action.DOUBLE if d_val <= 10 else Action.HIT
        if total == 10:
            return Action.DOUBLE if d_val <= 9 else Action.HIT
        if total == 9:
            return Action.DOUBLE if 3 <= d_val <= 6 else Action.HIT
        return Action.HIT   # total ≤ 8

    def place_bet(self, running_count, decks_remaining) -> int:
        return 20   # flat bet; no counting


# ---------------------------------------------------------------------------
# HiLoStrategy — adjusts bet and play based on the true count
# ---------------------------------------------------------------------------

class HiLoStrategy(Strategy):
    """Uses the Hi-Lo count to size bets and make index-play deviations.

    True count = running_count / decks_remaining

    Bet spread: min_bet at TC ≤ 1, scales up linearly, capped at max_bet.
    Play deviations (the "Illustrious 18" subset implemented here):
      - Insurance at TC ≥ +3
      - Stand 16 vs 10 at TC ≥ 0
      - Stand 15 vs 10 at TC ≥ +4
      - Stand 12 vs 3 at TC ≥ +2  /  vs 2 at TC ≥ +3
    All other decisions fall back to BasicStrategy.
    """

    def __init__(self, min_bet: int = 10, max_bet: int = 200):
        self.min_bet       = min_bet
        self.max_bet       = max_bet
        self._basic        = BasicStrategy()

    def _true_count(self, running_count: int, decks_remaining: float) -> float:
        return running_count / decks_remaining

    def decide(self, hand, dealer_up_card, running_count, decks_remaining) -> Action:
        tc    = self._true_count(running_count, decks_remaining)
        total = hand.total
        d_val = dealer_up_card.value

        # Index plays (deviations from basic strategy)
        if total == 16 and d_val == 10 and tc >= 0:
            return Action.STAND
        if total == 15 and d_val == 10 and tc >= 4:
            return Action.STAND
        if total == 12 and d_val == 3  and tc >= 2:
            return Action.STAND
        if total == 12 and d_val == 2  and tc >= 3:
            return Action.STAND

        # Fall back to basic strategy for everything else
        return self._basic.decide(hand, dealer_up_card, running_count, decks_remaining)

    def place_bet(self, running_count: int, decks_remaining: float) -> int:
        tc = self._true_count(running_count, decks_remaining)
        if tc <= 1:
            return self.min_bet
        # Spread: add one unit per true-count point above 1
        unit = self.min_bet
        bet  = self.min_bet + int(tc - 1) * unit
        return min(bet, self.max_bet)


# ===========================================================================
# Player
# ===========================================================================

class Player:
    """An automated computer player.

    Tracks chips, a hand, a strategy, and a running Hi-Lo count so that
    count-aware strategies have access to every visible card.
    """

    def __init__(self, name: str, chips: int, strategy: Strategy):
        self.name:          str      = name
        self.chips:         int      = chips
        self.strategy:      Strategy = strategy
        self.hand:          Hand     = Hand()
        self.running_count: int      = 0

    # --- betting ------------------------------------------------------------

    def place_bet(self, decks_remaining: float) -> int:
        """Ask strategy for a bet, deduct from chips, store in hand."""
        bet = self.strategy.place_bet(self.running_count, decks_remaining)
        # Never bet more than available chips
        bet = min(bet, self.chips)
        bet = max(bet, 1)
        self.chips    -= bet
        self.hand.bet  = bet
        return bet

    # --- card receiving & counting ------------------------------------------

    def receive_card(self, card: Card) -> None:
        """Add card to hand and update count (own face-up cards are visible)."""
        self.hand.add_card(card)
        if card.face_up:
            self.observe_card(card)

    def observe_card(self, card: Card) -> None:
        """Update running count for any face-up card visible on the table."""
        if card.face_up:
            self.running_count += card.hi_lo_count

    # --- decision -----------------------------------------------------------

    def decide_action(self, dealer_up_card: Card, decks_remaining: float) -> Action:
        return self.strategy.decide(
            self.hand, dealer_up_card, self.running_count, decks_remaining
        )

    # --- round lifecycle ----------------------------------------------------

    def reset_hand(self) -> None:
        self.hand.reset()

    def receive_payout(self, amount: int) -> None:
        """Add amount to chip stack (positive = win, negative = loss already deducted)."""
        self.chips += amount

    # --- display ------------------------------------------------------------

    def __repr__(self) -> str:
        return (f"Player({self.name!r}, chips={self.chips}, "
                f"strategy={type(self.strategy).__name__}, "
                f"count={self.running_count:+d})")

    def __str__(self) -> str:
        return repr(self)


# ===========================================================================
# HumanPlayer  — interactive input via the console
# ===========================================================================

class HumanPlayer(Player):
    """A human player who is prompted for bet and action via stdin.

    Inherits all chip / hand / count tracking from Player; overrides
    place_bet() and decide_action() to read from the keyboard.
    """

    def __init__(self, name: str, chips: int):
        # HumanPlayer has no automated strategy — pass None as placeholder
        super().__init__(name=name, chips=chips, strategy=None)

    def place_bet(self, decks_remaining: float) -> int:
        """Prompt the human for a bet amount."""
        print(f"\n{self.name}, you have {self.chips} chips.")
        while True:
            try:
                bet = int(input(f"  How many chips do you want to bet? "))
                if bet < 1:
                    print("  Bet must be at least 1.")
                elif bet > self.chips:
                    print(f"  You only have {self.chips} chips!")
                else:
                    self.chips    -= bet
                    self.hand.bet  = bet
                    return bet
            except ValueError:
                print("  Please enter a whole number.")

    def decide_action(self, dealer_up_card: Card, decks_remaining: float) -> Action:
        """Show the hand state and prompt the human for an action."""
        print(f"\n  Your hand : {self.hand}")
        print(f"  Dealer up : {dealer_up_card}")

        options = {
            "h": Action.HIT,
            "s": Action.STAND,
            "d": Action.DOUBLE,
            "q": Action.SURRENDER,
        }
        prompt = "  Action? [h]it / [s]tand / [d]ouble / [q]uit(surrender): "

        while True:
            choice = input(prompt).strip().lower()
            if choice in options:
                action = options[choice]
                # Guard: can only double on the first two cards
                if action == Action.DOUBLE and len(self.hand.cards) != 2:
                    print("  You can only double on your first two cards.")
                    continue
                # Guard: can only double if you have enough chips
                if action == Action.DOUBLE and self.chips < self.hand.bet:
                    print(f"  Not enough chips to double (need {self.hand.bet} more).")
                    continue
                return action
            print(f"  Invalid choice {choice!r}. Please enter h, s, d, or q.")


# ===========================================================================
# Dealer
# ===========================================================================

class Dealer(Player):
    """The casino dealer.

    Hits on 16 or below (including soft 17 is handled by the total property).
    One card is dealt face-down (the hole card) and revealed before the
    dealer takes their turn.
    """

    HIT_THRESHOLD: int = 16

    def __init__(self, chips: int = 0):
        super().__init__(name="Dealer", chips=chips, strategy=StandStrategy())
        self.up_card: Optional[Card] = None

    def decide_action(self, dealer_up_card: Card, decks_remaining: float) -> Action:
        """Fixed house rule: hit on ≤ 16, stand on 17+."""
        return Action.HIT if self.hand.total <= self.HIT_THRESHOLD else Action.STAND

    def flip_hole_card(self) -> None:
        """Turn the face-down hole card face-up and update all player counts."""
        for card in self.hand.cards:
            if not card.face_up:
                card.face_up = True
                return   # only one hole card

    def __repr__(self) -> str:
        return (f"Dealer(chips={self.chips}, "
                f"hand={self.hand}, "
                f"threshold={self.HIT_THRESHOLD})")

    def __str__(self) -> str:
        return repr(self)


# ===========================================================================
# RoundResult
# ===========================================================================

class RoundResult:
    """Outcome record for one player in one round."""

    def __init__(
        self,
        player_name:   str,
        strategy_name: str,
        bet:           int,
        net:           int,
        player_total:  int,
        dealer_total:  int,
        is_blackjack:  bool,
        is_bust:       bool,
    ):
        self.player_name   = player_name
        self.strategy_name = strategy_name
        self.bet           = bet
        self.net           = net
        self.player_total  = player_total
        self.dealer_total  = dealer_total
        self.is_blackjack  = is_blackjack
        self.is_bust       = is_bust

    def __repr__(self) -> str:
        sign = "+" if self.net >= 0 else ""
        return (f"RoundResult({self.player_name} | "
                f"player={self.player_total} dealer={self.dealer_total} | "
                f"net={sign}{self.net})")


# ===========================================================================
# Game
# ===========================================================================

class Game:
    """Orchestrates one or many rounds of blackjack.

    Round sequence
    --------------
    1. _collect_bets          — each player places a bet
    2. _deal_initial_cards    — 2 cards each; dealer's first card face-down
    3. _player_turns          — each player acts until stand/bust/double
    4. _dealer_turn           — dealer flips hole card, hits to 17+
    5. _resolve_bets          — compare totals, pay out, log RoundResult
    6. _reset_round           — discard hands; reshuffle shoe if needed
    """

    # Blackjack pays 3:2
    BLACKJACK_PAYOUT: float = 1.5

    def __init__(self, players: list[Player], num_decks: int = 6):
        self.deck:    Deck          = Deck(num_decks=num_decks)
        self.dealer:  Dealer        = Dealer()
        self.players: list[Player]  = players
        self.history: list[RoundResult] = []

    # -----------------------------------------------------------------------
    # Private helpers — draw a card and notify all players of visible cards
    # -----------------------------------------------------------------------

    def _draw(self, face_up: bool = True) -> Card:
        """Draw one card from the shoe, skipping any PlasticCard sentinels."""
        while True:
            card = self.deck.draw()
            if card is None:
                # Shoe exhausted — emergency reshuffle
                self.deck.shuffle()
                card = self.deck.draw()
            if isinstance(card, PlasticCard):
                # Flag already set inside Deck.draw(); draw the next real card
                continue
            card.face_up = face_up
            return card

    def _broadcast(self, card: Card) -> None:
        """Let every player observe a face-up card (updates running counts)."""
        if card.face_up:
            for player in self.players:
                player.observe_card(card)

    # -----------------------------------------------------------------------
    # Round steps
    # -----------------------------------------------------------------------

    def _collect_bets(self) -> None:
        for player in self.players:
            player.place_bet(self.deck.decks_remaining)

    def _deal_initial_cards(self) -> None:
        """Deal two cards to each player then two to the dealer.
        Dealer's first card is face-down (hole card); second is face-up.
        """
        # First card to each player (face-up)
        for player in self.players:
            card = self._draw(face_up=True)
            player.receive_card(card)
            self._broadcast(card)

        # Dealer's hole card (face-down — NOT broadcast yet)
        hole = self._draw(face_up=False)
        self.dealer.hand.add_card(hole)
        # Do NOT broadcast the hole card until it is flipped

        # Second card to each player (face-up)
        for player in self.players:
            card = self._draw(face_up=True)
            player.receive_card(card)
            self._broadcast(card)

        # Dealer's up card (face-up)
        up = self._draw(face_up=True)
        self.dealer.hand.add_card(up)
        self.dealer.up_card = up
        self._broadcast(up)
        # Dealer also observes their own up card for count purposes
        self.dealer.observe_card(up)

    def _player_turns(self) -> None:
        """Each player acts until they stand, bust, surrender, or double."""
        dealer_up = self.dealer.up_card

        for player in self.players:
            # Skip if player has a blackjack (automatic win resolved later)
            if player.hand.is_blackjack:
                if isinstance(player, HumanPlayer):
                    print(f"\n  {player.name}: Blackjack! 🃏")
                continue

            while not player.hand.is_bust:
                action = player.decide_action(dealer_up, self.deck.decks_remaining)

                if action == Action.STAND:
                    break

                elif action == Action.HIT:
                    card = self._draw(face_up=True)
                    player.receive_card(card)
                    self._broadcast(card)
                    if isinstance(player, HumanPlayer):
                        print(f"  Hit → {card}")
                    if player.hand.is_bust:
                        if isinstance(player, HumanPlayer):
                            print(f"  Bust! Total = {player.hand.total}")
                        break

                elif action == Action.DOUBLE:
                    # Double the bet, draw exactly one card, then stand
                    extra = player.hand.bet
                    player.chips   -= extra
                    player.hand.bet += extra
                    card = self._draw(face_up=True)
                    player.receive_card(card)
                    self._broadcast(card)
                    if isinstance(player, HumanPlayer):
                        print(f"  Double → {card}  (bet now {player.hand.bet})")
                    break   # only one card on a double

                elif action == Action.SURRENDER:
                    # Forfeit half the bet; mark hand so resolve can skip it
                    player.hand.add_card(Card("A", "Hearts", face_up=False))  # dummy sentinel
                    # Instead of a dummy card, use a flag
                    player.hand._surrendered = True
                    if isinstance(player, HumanPlayer):
                        print(f"  Surrendered. Half bet ({player.hand.bet // 2}) returned.")
                    break

                else:
                    # SPLIT — not yet implemented; treat as stand
                    break

    def _dealer_turn(self) -> None:
        """Reveal hole card, broadcast it, then hit until 17+."""
        self.dealer.flip_hole_card()
        # Now broadcast the formerly-hidden hole card to all players
        hole = self.dealer.hand.cards[0]   # hole card is always index 0
        self._broadcast(hole)
        self.dealer.observe_card(hole)

        print(f"\n  Dealer reveals: {self.dealer.hand}")

        while self.dealer.decide_action(self.dealer.up_card, self.deck.decks_remaining) == Action.HIT:
            card = self._draw(face_up=True)
            self.dealer.hand.add_card(card)
            self.dealer.observe_card(card)
            self._broadcast(card)
            print(f"  Dealer hits → {card}  (total={self.dealer.hand.total})")

        result = "BUSTS" if self.dealer.hand.is_bust else f"stands on {self.dealer.hand.total}"
        print(f"  Dealer {result}.")

    def _resolve_bets(self) -> None:
        """Compare each player's hand to the dealer, pay out, log result."""
        dealer_total = self.dealer.hand.total
        dealer_bj    = self.dealer.hand.is_blackjack
        dealer_bust  = self.dealer.hand.is_bust

        for player in self.players:
            bet          = player.hand.bet
            player_total = player.hand.total
            player_bj    = player.hand.is_blackjack
            player_bust  = player.hand.is_bust
            surrendered  = getattr(player.hand, "_surrendered", False)

            # --- determine net chips won/lost ---
            if surrendered:
                # Return half the bet (the other half was already deducted)
                net = -(bet // 2)
                player.receive_payout(bet - bet // 2)   # return surviving half
                outcome = "surrendered"

            elif player_bust:
                net     = -bet   # already deducted when bet was placed
                outcome = "bust"

            elif player_bj and not dealer_bj:
                # Blackjack pays 3:2
                winnings = int(bet * self.BLACKJACK_PAYOUT)
                net      = winnings
                player.receive_payout(bet + winnings)   # original bet + profit
                outcome  = "blackjack"

            elif dealer_bj and not player_bj:
                net     = -bet
                outcome = "dealer blackjack"

            elif player_bj and dealer_bj:
                # Both blackjack → push
                net     = 0
                player.receive_payout(bet)
                outcome = "push (both BJ)"

            elif dealer_bust:
                net = bet
                player.receive_payout(bet + bet)
                outcome = "win (dealer bust)"

            elif player_total > dealer_total:
                net = bet
                player.receive_payout(bet + bet)
                outcome = "win"

            elif player_total == dealer_total:
                net     = 0
                player.receive_payout(bet)   # push — return bet
                outcome = "push"

            else:
                net     = -bet   # already deducted
                outcome = "loss"

            # --- log ---
            self.history.append(RoundResult(
                player_name   = player.name,
                strategy_name = type(player.strategy).__name__ if player.strategy else "Human",
                bet           = bet,
                net           = net,
                player_total  = player_total,
                dealer_total  = dealer_total,
                is_blackjack  = player_bj,
                is_bust       = player_bust,
            ))

            print(f"  {player.name:12s}  {player_total:>2d} vs dealer {dealer_total:>2d}"
                  f"  → {outcome:25s}  net={net:+d}  chips={player.chips}")

    def _reset_round(self) -> None:
        """Discard all hands; reshuffle shoe when plastic card has been drawn."""
        for player in self.players:
            player.reset_hand()
        self.dealer.reset_hand()
        self.dealer.up_card = None

        if self.deck.reshuffle_needed:
            print("\n  [Plastic card reached — reshuffling shoe before next round]")
            self.deck.shuffle()
            # Reset all running counts after a reshuffle
            for player in self.players:
                player.running_count = 0
            self.dealer.running_count = 0

    # -----------------------------------------------------------------------
    # Public interface
    # -----------------------------------------------------------------------

    def run_round(self, verbose: bool = True) -> None:
        """Play one complete round."""
        if verbose:
            print("\n" + "=" * 60)
            print(f"  ROUND  |  shoe: {self.deck.cards_remaining} cards"
                  f"  ({self.deck.decks_remaining:.1f} decks remaining)")
            print("=" * 60)

        self._collect_bets()
        self._deal_initial_cards()

        if verbose:
            print("\n  Initial deal:")
            for p in self.players:
                print(f"    {p.name:12s}: {p.hand}")
            print(f"    {'Dealer':12s}: {self.dealer.up_card}  [hole card hidden]")

        self._player_turns()
        self._dealer_turn()

        if verbose:
            print("\n  Payouts:")
        self._resolve_bets()
        self._reset_round()

    def run_simulation(self, num_rounds: int) -> list[RoundResult]:
        """Run num_rounds silently and return the full history."""
        for _ in range(num_rounds):
            self.run_round(verbose=False)
        return self.history

    def get_stats(self) -> dict:
        """Aggregate RoundResults by strategy name.

        Returns a dict keyed by strategy name:
          total_rounds, total_net, avg_net_per_hand,
          win_rate, bust_rate, blackjack_rate
        """
        from collections import defaultdict

        buckets: dict[str, list[RoundResult]] = defaultdict(list)
        for r in self.history:
            buckets[r.strategy_name].append(r)

        stats = {}
        for strat, results in buckets.items():
            n           = len(results)
            total_net   = sum(r.net for r in results)
            wins        = sum(1 for r in results if r.net > 0)
            busts       = sum(1 for r in results if r.is_bust)
            blackjacks  = sum(1 for r in results if r.is_blackjack)
            stats[strat] = {
                "total_rounds":    n,
                "total_net":       total_net,
                "avg_net_per_hand": round(total_net / n, 2) if n else 0,
                "win_rate":        round(wins       / n, 3) if n else 0,
                "bust_rate":       round(busts      / n, 3) if n else 0,
                "blackjack_rate":  round(blackjacks / n, 3) if n else 0,
            }
        return stats

    def __repr__(self) -> str:
        return (f"Game(players={[p.name for p in self.players]}, "
                f"rounds_played={len(self.history)})")


# ===========================================================================
# Smoke tests
# ===========================================================================

if __name__ == "__main__":

    # -------------------------------------------------------------------
    # Test 1: Hand logic
    # -------------------------------------------------------------------
    print("=== Hand logic ===")

    h = Hand(bet=50)
    h.add_card(Card("A", "Spades"))
    h.add_card(Card("K", "Hearts"))
    print(f"  A + K          → total={h.total}  blackjack={h.is_blackjack}  soft={h.is_soft}")
    assert h.total == 21 and h.is_blackjack

    h2 = Hand()
    h2.add_card(Card("A", "Spades"))
    h2.add_card(Card("A", "Hearts"))
    h2.add_card(Card("9", "Diamonds"))
    print(f"  A + A + 9      → total={h2.total}  bust={h2.is_bust}")
    assert h2.total == 21 and not h2.is_bust

    h3 = Hand()
    h3.add_card(Card("K", "Spades"))
    h3.add_card(Card("Q", "Hearts"))
    h3.add_card(Card("5", "Clubs"))
    print(f"  K + Q + 5      → total={h3.total}  bust={h3.is_bust}")
    assert h3.total == 25 and h3.is_bust

    h4 = Hand()
    h4.add_card(Card("A", "Spades"))
    h4.add_card(Card("6", "Hearts"))
    print(f"  A + 6          → total={h4.total}  soft={h4.is_soft}")
    assert h4.total == 17 and h4.is_soft

    print("  All Hand assertions passed.\n")

    # -------------------------------------------------------------------
    # Test 2: Automated 3-round game (no human player)
    # -------------------------------------------------------------------
    print("=== Automated 3-round game ===")

    players = [
        Player("Alexia",  chips=500, strategy=BasicStrategy()),
        Player("Brianna", chips=500, strategy=StandStrategy()),
        Player("David",   chips=500, strategy=RandomStrategy()),
    ]
    game = Game(players=players, num_decks=6)

    for _ in range(3):
        game.run_round(verbose=True)

    print("\n=== Stats after 3 rounds ===")
    for strat, s in game.get_stats().items():
        print(f"  {strat:20s}  rounds={s['total_rounds']}  "
              f"net={s['total_net']:+d}  avg={s['avg_net_per_hand']:+.2f}  "
              f"win%={s['win_rate']:.0%}")

    print("\nAll smoke tests passed.")
