import pandas as pd
import numpy as np
from loguru import logger
from termcolor import colored


class QLearningTrader:
    def __init__(
        self,
        num_actions,
        num_features,
        learning_rate,
        discount_factor,
        exploration_prob,
    ):

        self.num_actions = num_actions  # 3: Buy, Sell & Hold
        self.num_features = num_features  # OLHC
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.exploration_prob = exploration_prob
        self.cumulative_reward = 0

        # Initialize Q-table with zeros
        self.q_table = np.zeros((num_actions, num_features))

        # Initialize state and action
        self.current_state = None
        self.current_action = None

    def choose_action(self, state):
        # Exploration-exploitation trade-off
        if np.random.uniform(0, 1) < self.exploration_prob:
            return np.random.choice(self.num_actions)  # Explore
        else:
            feature_index = np.argmax(state)
            return np.argmax(self.q_table[:, feature_index])  # Exploit

    def calculate_reward(self, action, current_close, next_close):
        price_change = (next_close - current_close) / current_close

        if action == 0:  # Buy
            return price_change  # Profit if price increases, loss if price decreases
        elif action == 1:  # Sell
            return -price_change  # Profit if price decreases, loss if price increases
        else:
            if price_change > 0:
                return price_change
            else:
                return -price_change

    def take_action(self, action, reward):
        # Update Q-table based on the observed reward
        if self.current_action is not None:
            feature_index = np.argmax(self.current_state)
            current_q_value = self.q_table[self.current_action, feature_index]
            new_q_value = (
                1 - self.learning_rate
            ) * current_q_value + self.learning_rate * (
                reward + self.discount_factor * np.max(self.q_table[:, feature_index])
            )
            self.q_table[self.current_action, feature_index] = new_q_value

        # Update current state and action
        self.current_state = None
        self.current_action = action

    def train(self, historical_data):
        logger.info("Training the Q-learning model...")

        for i in range(len(historical_data) - 1):
            current_close = historical_data.iloc[i]["Close"]
            next_close = historical_data.iloc[i + 1]["Close"]

            # Choose an action
            action = self.choose_action(current_close)

            # Calculate the reward
            reward = self.calculate_reward(action, current_close, next_close)

            # Update cumulative reward
            self.cumulative_reward += reward

            # Take the action and update the Q-table
            self.take_action(action, reward)

            # Log the state, action, reward, updated Q-value, and cumulative reward

            print(
                colored("State: ", "green")
                + "\n"
                + colored(f"{current_close}", "white")
                + colored(", Action: ", "green")
                + colored(f"{action}", "white")
                + colored(", Reward: ", "green")
                + colored(f"{reward}", "white")
                + colored(", Updated Q-value: ", "green")
                + colored(f"{self.q_table[action, np.argmax(current_close)]}", "white")
                + colored(", Cumulative reward: ", "green")
                + colored(f"{self.cumulative_reward}", "white")
            )

        logger.info("Training complete.")

    def update(self, historical_df, new_data_df):
        self.cumulative_reward = 0
        if len(new_data_df) != 1:
            raise ValueError("New data DataFrame must contain exactly one row of data.")

        # The current state is the last row of the historical data
        current_state = historical_df.iloc[-1]

        # The new state is the incoming data
        next_state = new_data_df.iloc[0]

        # Choose an action based on the current state
        action = self.choose_action(current_state)

        # Add print statement for the action
        if action == 0:
            print("Buy signal detected.")
        elif action == 1:
            print("Sell signal detected.")
        else:  # Assuming 2 is for Hold
            print("Hold signal detected.")

        # Calculate the reward based on the action taken and the observed price movement
        reward = self.calculate_reward(
            action, current_state["Close"], next_state["Close"]
        )

        # Update cumulative reward
        self.cumulative_reward += reward

        # Take the action and update the Q-table
        self.take_action(action, reward)

        # Log the state, action, reward, updated Q-value, and cumulative reward
        print(
            colored("State: ", "green")
            + "\n"
            + colored(f"{current_state}", "white")
            + colored(", Action: ", "green")
            + colored(f"{action}", "white")
            + colored(", Reward: ", "green")
            + colored(f"{reward}", "white")
            + colored(", Updated Q-value: ", "green")
            + colored(f"{self.q_table[action, np.argmax(current_state)]}", "white")
            + colored(", Cumulative reward: ", "green")
            + colored(f"{self.cumulative_reward}", "white")
        )

        return action
