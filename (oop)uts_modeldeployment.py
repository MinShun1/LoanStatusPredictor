# -*- coding: utf-8 -*-
"""(OOP)UTS_ModelDeployment.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1ykmaKiEN49Kes6JWxfotgUizIdEt3x8N
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler, LabelEncoder, OneHotEncoder, RobustScaler
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import confusion_matrix, classification_report, ConfusionMatrixDisplay
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.impute import SimpleImputer
from imblearn.over_sampling import SMOTE

class LoanModelTrainer:
    def __init__(self, df):
        self.df = df.copy()
        self.x_train = None
        self.x_test = None
        self.y_train = None
        self.y_test = None
        self.x_train_resampled = None
        self.y_train_resampled = None
        self.x_test_resampled = None
        self.y_test_resampled = None
        self.scaler = RobustScaler()
        self.imputer = SimpleImputer(strategy='median')
        self.encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')

    def preprocess(self):
        self._encode_features()

        X = self.df.drop('loan_status', axis=1)
        y = self.df['loan_status']

        self.x_train, self.x_test, self.y_train, self.y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        self.x_train = pd.DataFrame(self.imputer.fit_transform(self.x_train), columns=self.x_train.columns)
        self.x_test = pd.DataFrame(self.imputer.transform(self.x_test), columns=self.x_test.columns)

        self._fix_anomalies()

        self.x_train = pd.DataFrame(self.scaler.fit_transform(self.x_train), columns=self.x_train.columns)
        self.x_test = pd.DataFrame(self.scaler.transform(self.x_test), columns=self.x_test.columns)

    def _fix_anomalies(self):
        median_age = self.x_train[self.x_train['person_age'] <= 100]['person_age'].median()
        self.x_train.loc[self.x_train['person_age'] > 100, 'person_age'] = median_age
        self.x_test.loc[self.x_test['person_age'] > 100, 'person_age'] = median_age

        median_exp = self.x_train[self.x_train['person_emp_exp'] <= 75]['person_emp_exp'].median()
        self.x_train.loc[self.x_train['person_emp_exp'] > 75, 'person_emp_exp'] = median_exp
        self.x_test.loc[self.x_test['person_emp_exp'] > 75, 'person_emp_exp'] = median_exp

    def _encode_features(self):
        self.df['person_gender'] = self.df['person_gender'].replace({
            'Male': 'male',
            'fe male': 'female'
        })

        education_map = {
            'High School': 0,
            'Associate': 1,
            'Bachelor': 2,
            'Master': 3,
            'Doctorate': 4
        }
        self.df['person_education'] = self.df['person_education'].map(education_map)
        self.df['previous_loan_defaults_on_file'] = self.df['previous_loan_defaults_on_file'].map({'No': 0, 'Yes': 1})
        self.df['person_gender'] = self.df['person_gender'].map({'female': 0, 'male': 1})

        cat_features = ['person_home_ownership', 'loan_intent']
        for feature in cat_features:
            encoded = self.encoder.fit_transform(self.df[[feature]])
            encoded_df = pd.DataFrame(
                encoded,
                columns=self.encoder.get_feature_names_out([feature]),
                index=self.df.index
            )
            self.df = pd.concat([self.df.drop(columns=[feature]), encoded_df], axis=1)

    def apply_smote(self):
        print("Distribusi sebelum SMOTE:")
        print(pd.Series(self.y_train).value_counts())

        smote = SMOTE(random_state=42, k_neighbors=2)
        self.x_train_resampled, self.y_train_resampled = smote.fit_resample(self.x_train, self.y_train)
        self.x_test_resampled, self.y_test_resampled = smote.fit_resample(self.x_test, self.y_test)

        print("Distribusi setelah SMOTE:")
        print(pd.Series(self.y_train_resampled).value_counts())

    def train_random_forest(self):
        model = RandomForestClassifier(random_state=42)
        model.fit(self.x_train_resampled, self.y_train_resampled)
        y_pred = model.predict(self.x_test)

        print("\nClassification Report (Random Forest):")
        print(classification_report(self.y_test, y_pred))

        cm = confusion_matrix(self.y_test, y_pred)
        ConfusionMatrixDisplay(cm).plot()

    def train_xgboost_with_gridsearch(self):
        xgb_params = {
            'learning_rate': [0.01, 0.1, 0.2],
            'max_depth': [3, 5, 7],
            'n_estimators': [50, 100, 200]
        }

        xgb = XGBClassifier(random_state=42, eval_metric='mlogloss')
        xgb_grid = GridSearchCV(xgb, xgb_params, cv=3, scoring='f1_macro', verbose=0)
        xgb_grid.fit(self.x_train_resampled, self.y_train_resampled)

        best_model = xgb_grid.best_estimator_
        print("Best XGBoost Parameters:", xgb_grid.best_params_)

        y_pred = best_model.predict(self.x_test)
        print("\nClassification Report (XGBoost):")
        print(classification_report(self.y_test, y_pred))

    def train_all_models(self):
        print(">>> Preprocessing data...")
        self.preprocess()

        print("\n>>> Applying SMOTE...")
        self.apply_smote()

        print("\n>>> Training Random Forest...")
        self.train_random_forest()

        print("\n>>> Training XGBoost with GridSearchCV...")
        self.train_xgboost_with_gridsearch()

df = pd.read_csv(r"C:\Users\minli\Desktop\BINUS\SMT 4\Model Deployment\UTS\Dataset_A_loan.csv")

trainer = LoanModelTrainer(df)
trainer.train_all_models()

