
from __future__ import annotations
import random
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional

Suits       = ("Hearts", "Diamonds", "Spades", "Clubs")
Ranks       = ("2","3","4","5","6","7","8","9","10","J","Q","K","A")
Rank_values  = {"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,"10":10,
                "J":10,"Q":10,"K":10,"A":11}

class Action(Enum):
    HIT       = "hit"
    STAND     = "stand"
    DOUBLE    = "double"
    SPLIT     = "split"
    SURRENDER = "surrender"

class Card:
    def __init__(self, rank: str, suit: str, face_up: bool = True):
        self.rank    = rank
        self.suit    = suit
        self.face_up = face_up

    @property
    def value(self) -> int:
        return Rank_values[self.rank]

    @property
    def hi_lo_count(self) -> int:
        if self.rank in ("2","3","4","5","6"):
            return 1
        if self.rank in ("10","J","Q","K","A"):
            return -1
        return 0

    def __repr__(self) -> str:
        if not self.face_up:
            return "[hidden]"
        return f"[{self.rank} of {self.suit}]"


class PlasticCard(Card):
    def __init__(self):
        super().__init__("Plastic", "None", face_up=True)

    @property
    def value(self) -> int:
        return 0

    @property
    def hi_lo_count(self) -> int:
        return 0

    def __repr__(self) -> str:
        return "[Plastic]"


class Deck:
    def __init__(self, num_decks: int = 6, plastic_zone: tuple = (60, 80)):
        self.num_decks   = num_decks
        self.plastic_zone = plastic_zone
        self.cards: list[Card] = []
        self.reshuffle_needed  = False
        self.shuffle()

    def shuffle(self) -> None:
        self.cards = [Card(r, s) for _ in range(self.num_decks)
                      for s in Suits for r in Ranks]
        random.shuffle(self.cards)
        pos = random.randint(
            len(self.cards) - self.plastic_zone[1],
            len(self.cards) - self.plastic_zone[0]
        )
        self.cards.insert(pos, PlasticCard())
        self.reshuffle_needed = False

    def draw(self) -> Card:
        return self.cards.pop(0)

    @property
    def cards_remaining(self) -> int:
        return len(self.cards)

    @property
    def decks_remaining(self) -> float:
        return self.cards_remaining / 52

class Hand:
    def __init__(self, bet: int = 0):
        self.cards: list[Card] = []
        self.bet   = bet

    def add_card(self, card: Card) -> None:
        self.cards.append(card)

    def reset(self) -> None:
        self.cards = []
        self.bet   = 0

    @property
    def total(self) -> int:
        total = sum(c.value for c in self.cards)
        aces  = sum(1 for c in self.cards if c.rank == "A")
        while total > 21 and aces:
            total -= 10
            aces  -= 1
        return total

    @property
    def is_bust(self) -> bool:
        return self.total > 21

    @property
    def is_blackjack(self) -> bool:
        return (len(self.cards) == 2
                and any(c.rank == "A" for c in self.cards)
                and any(c.value == 10 for c in self.cards))

    @property
    def is_soft(self) -> bool:
        total = sum(c.value for c in self.cards)
        aces  = sum(1 for c in self.cards if c.rank == "A")
        while total > 21 and aces:
            total -= 10
            aces  -= 1
        return aces > 0

    @property
    def is_pair(self) -> bool:
        return len(self.cards) == 2 and self.cards[0].rank == self.cards[1].rank

    @property
    def running_count(self) -> int:
        return sum(c.hi_lo_count for c in self.cards if c.face_up)

    def __repr__(self) -> str:
        return (f"Hand({self.cards}  total={self.total}  bet={self.bet})")

class Strategy(ABC):
    @abstractmethod
    def place_bet(self, player, decks_remaining: float) -> int:
        pass

    @abstractmethod
    def decide(self, hand, dealer_up_card, decks_remaining: float) -> Action:
        pass

class StandStrategy(Strategy):
    def place_bet(self, player, decks_remaining: float) -> int:
        return min(10, player.chips)

    def decide(self, hand, dealer_up_card, decks_remaining: float) -> Action:
        return Action.STAND


class RandomStrategy(Strategy):
    def place_bet(self, player, decks_remaining: float) -> int:
        return min(random.choice([10, 20, 25, 50]), player.chips)

    def decide(self, hand, dealer_up_card, decks_remaining: float) -> Action:
        return random.choice([Action.HIT, Action.STAND])


class BasicStrategy(Strategy):
    def place_bet(self, player, decks_remaining: float) -> int:
        return min(20, player.chips)

    def decide(self, hand, dealer_up_card, decks_remaining: float) -> Action:
        total      = hand.total
        dealer_val = dealer_up_card.value
        is_soft    = hand.is_soft

        if is_soft:
            if total >= 19:
                return Action.STAND
            if total == 18 and dealer_val in [2, 7, 8]:
                return Action.STAND
            return Action.HIT

        if total >= 17:
            return Action.STAND
        if total >= 13 and dealer_val in [2, 3, 4, 5, 6]:
            return Action.STAND
        if total == 12 and dealer_val in [4, 5, 6]:
            return Action.STAND
        if total == 11:
            return Action.DOUBLE if dealer_val <= 10 else Action.HIT
        if total == 10:
            return Action.DOUBLE if dealer_val <= 9 else Action.HIT
        if total == 9 and dealer_val in [3, 4, 5, 6]:
            return Action.DOUBLE
        return Action.HIT


class HiLoStrategy(Strategy):
    def __init__(self, min_bet: int = 10, max_bet: int = 200):
        self.min_bet = min_bet
        self.max_bet = max_bet

    def place_bet(self, player, decks_remaining: float) -> int:
        tc   = player.running_count / max(decks_remaining, 0.5)
        unit = (self.max_bet - self.min_bet) / 10
        bet  = self.min_bet + max(0, (tc - 1)) * unit
        return min(int(bet), player.chips)

    def decide(self, hand, dealer_up_card, decks_remaining: float) -> Action:
        total      = hand.total
        dealer_val = dealer_up_card.value
        tc         = player_running_count = hand.running_count / max(decks_remaining, 0.5)

        # Index plays
        if total == 16 and dealer_val == 10 and tc >= 0:
            return Action.STAND
        if total == 15 and dealer_val == 10 and tc >= 4:
            return Action.STAND
        if total == 12 and dealer_val == 3  and tc >= 2:
            return Action.STAND
        if total == 12 and dealer_val == 2  and tc >= 3:
            return Action.STAND

        return BasicStrategy().decide(hand, dealer_up_card, decks_remaining)

class Player:
    def __init__(self, name: str, chips: int = 500, strategy: Strategy = None):
        self.name          = name
        self.chips         = chips
        self.strategy      = strategy or StandStrategy()
        self.hand          = Hand()
        self.running_count = 0

    def place_bet(self, decks_remaining: float) -> None:
        bet = self.strategy.place_bet(self, decks_remaining)
        bet = max(1, min(bet, self.chips))
        self.chips    -= bet
        self.hand.bet  = bet

    def receive_card(self, card: Card) -> None:
        self.hand.add_card(card)
        if card.face_up:
            self.observe_card(card)

    def observe_card(self, card: Card) -> None:
        if card.face_up:
            self.running_count += card.hi_lo_count

    def decide_action(self, dealer_up_card: Card, decks_remaining: float) -> Action:
        return self.strategy.decide(self.hand, dealer_up_card, decks_remaining)

    def reset_hand(self) -> None:
        self.hand.reset()

    def receive_payout(self, amount: int) -> None:
        self.chips += amount

    @property
    def up_card(self) -> Optional[Card]:
        return self.hand.cards[0] if self.hand.cards else None

    def __repr__(self) -> str:
        return f"Player({self.name}, chips={self.chips})"


class Dealer(Player):
    def __init__(self):
        super().__init__("Dealer", chips=999999, strategy=StandStrategy())

    def decide_action(self, dealer_up_card: Card, decks_remaining: float) -> Action:
        if self.hand.total <= 16:
            return Action.HIT
        return Action.STAND

    def flip_hole_card(self) -> None:
        for card in self.hand.cards:
            if not card.face_up:
                card.face_up = True
                return

class RoundResult:
    def __init__(self, player_name, strategy_name, player_total,
                 dealer_total, net, is_blackjack, is_bust):
        self.player_name   = player_name
        self.strategy_name = strategy_name
        self.player_total  = player_total
        self.dealer_total  = dealer_total
        self.net           = net
        self.is_blackjack  = is_blackjack
        self.is_bust       = is_bust

    def __repr__(self) -> str:
        sign = "+" if self.net >= 0 else ""
        return (f"RoundResult({self.player_name} | "
                f"player={self.player_total} dealer={self.dealer_total} | "
                f"net={sign}{self.net})")


class Game:
    BLACKJACK_PAYOUT: float = 1.5

    def __init__(self, players: list, num_decks: int = 6):
        self.deck    = Deck(num_decks=num_decks)
        self.dealer  = Dealer()
        self.players = players
        self.history: list[RoundResult] = []

    def _draw(self, face_up: bool = True) -> Card:
        while True:
            card = self.deck.draw()
            if isinstance(card, PlasticCard):
                self.deck.reshuffle_needed = True
                continue
            card.face_up = face_up
            return card

    def _broadcast(self, card: Card) -> None:
        if card.face_up:
            for player in self.players:
                player.observe_card(card)

    def _collect_bets(self) -> None:
        for player in self.players:
            player.place_bet(self.deck.decks_remaining)

    def _deal_initial_cards(self) -> None:
        for player in self.players:
            c = self._draw(face_up=True)
            player.receive_card(c)
            self._broadcast(c)
        hole = self._draw(face_up=False)
        self.dealer.hand.add_card(hole)
        # Each player gets second card
        for player in self.players:
            c = self._draw(face_up=True)
            player.receive_card(c)
            self._broadcast(c)
        up = self._draw(face_up=True)
        self.dealer.hand.add_card(up)
        self._broadcast(up)

    def _player_turns(self) -> None:
        for player in self.players:
            if player.hand.is_blackjack:
                continue
            while True:
                action = player.decide_action(
                    self.dealer.up_card, self.deck.decks_remaining)
                if action == Action.STAND:
                    break
                elif action == Action.HIT:
                    c = self._draw()
                    player.receive_card(c)
                    self._broadcast(c)
                    if player.hand.is_bust:
                        break
                elif action == Action.DOUBLE:
                    extra = min(player.hand.bet, player.chips)
                    player.chips   -= extra
                    player.hand.bet += extra
                    c = self._draw()
                    player.receive_card(c)
                    self._broadcast(c)
                    break
                elif action == Action.SURRENDER:
                    player.hand._surrendered = True
                    break
                else:
                    break

    def _dealer_turn(self) -> None:
        self.dealer.flip_hole_card()
        hole = self.dealer.hand.cards[0]
        self._broadcast(hole)
        while self.dealer.hand.total <= 16:
            c = self._draw()
            self.dealer.hand.add_card(c)
            self._broadcast(c)

    def _resolve_bets(self, verbose: bool = False) -> None:
        dealer_total = self.dealer.hand.total
        dealer_bj    = self.dealer.hand.is_blackjack

        if verbose:
            if self.dealer.hand.is_bust:
                print(f"  Dealer BUSTS.")
            else:
                print(f"  Dealer stands on {dealer_total}.")

        for player in self.players:
            bet          = player.hand.bet
            player_total = player.hand.total
            player_bj    = player.hand.is_blackjack
            surrendered  = getattr(player.hand, "_surrendered", False)

            if surrendered:
                payout = bet // 2
                net    = payout - bet
                outcome = "surrender"
            elif player.hand.is_bust:
                payout  = 0
                net     = -bet
                outcome = "bust"
            elif player_bj and dealer_bj:
                payout  = bet
                net     = 0
                outcome = "push (both BJ)"
            elif player_bj:
                payout  = bet + int(bet * self.BLACKJACK_PAYOUT)
                net     = int(bet * self.BLACKJACK_PAYOUT)
                outcome = "blackjack"
            elif dealer_bj:
                payout  = 0
                net     = -bet
                outcome = "dealer blackjack"
            elif self.dealer.hand.is_bust:
                payout  = bet * 2
                net     = bet
                outcome = "win (dealer bust)"
            elif player_total > dealer_total:
                payout  = bet * 2
                net     = bet
                outcome = "win"
            elif player_total == dealer_total:
                payout  = bet
                net     = 0
                outcome = "push"
            else:
                payout  = 0
                net     = -bet
                outcome = "loss"

            player.receive_payout(payout)

            if verbose:
                print(f"  {player.name:12s}  {player_total:>2d} vs dealer {dealer_total:<2d}"
                      f"  → {outcome:<22s}  net={net:+d}  chips={player.chips}")

            self.history.append(RoundResult(
                player_name   = player.name,
                strategy_name = player.strategy.__class__.__name__,
                player_total  = player_total,
                dealer_total  = dealer_total,
                net           = net,
                is_blackjack  = player_bj,
                is_bust       = player.hand.is_bust,
            ))

    def _reset_round(self) -> None:
        for player in self.players:
            player.reset_hand()
        self.dealer.reset_hand()
        if self.deck.reshuffle_needed:
            self.deck.shuffle()
            for player in self.players:
                player.running_count = 0
            self.dealer.running_count = 0

    def run_round(self, verbose: bool = True) -> None:
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
            print(f"\n  Dealer reveals: {self.dealer.hand}")
        self._resolve_bets(verbose=verbose)
        self._reset_round()

    def run_simulation(self, num_rounds: int) -> list:
        for _ in range(num_rounds):
            self.run_round(verbose=False)
        return self.history

    def get_stats(self) -> dict:
        from collections import defaultdict
        buckets = defaultdict(list)
        for r in self.history:
            buckets[r.strategy_name].append(r)

        stats = {}
        for strat, results in buckets.items():
            n          = len(results)
            total_net  = sum(r.net for r in results)
            wins       = sum(1 for r in results if r.net > 0)
            busts      = sum(1 for r in results if r.is_bust)
            blackjacks = sum(1 for r in results if r.is_blackjack)
            stats[strat] = {
                "total_rounds":     n,
                "total_net":        total_net,
                "avg_net_per_hand": round(total_net / n, 2) if n else 0,
                "win_rate":         round(wins       / n, 3) if n else 0,
                "bust_rate":        round(busts      / n, 3) if n else 0,
                "blackjack_rate":   round(blackjacks / n, 3) if n else 0,
            }
        return stats

    def __repr__(self) -> str:
        return (f"Game(players={[p.name for p in self.players]}, "
                f"rounds_played={len(self.history)})")
