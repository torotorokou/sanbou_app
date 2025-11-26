"""
UseCases package (アプリケーション層).

Clean Architecture における「UseCase」を定義します。
各 UseCase はビジネスロジックの手順（オーケストレーション）を記述し、
Port（抽象インターフェース）にのみ依存します。

👶 UseCase は「何をするか」を定義し、「どうやるか」は Port/Adapter に委譲します。
"""
