import optuna
import sys

study_name = sys.argv[1]
storage = sys.argv[2]

study = optuna.load_study(study_name=study_name, storage=storage)

print(f"\nStudy: {study_name}")
print(f"Total trials: {len(study.trials)}\n")

print("Trial Details:")
print("-" * 80)

for t in study.trials[:10]:
    print(f"\nTrial {t.number}:")
    print(f"  Value: {t.value:.4f}")
    print(f"  Params: {t.params}")
    print(f"  User attrs:")
    for key, val in t.user_attrs.items():
        print(f"    {key}: {val}")
