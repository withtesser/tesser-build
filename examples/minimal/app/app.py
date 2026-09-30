from __future__ import annotations

import collections.abc as collections_abc
import os
import typing

import tesser.app as ts

import alpha.adapters.gateways as alpha_gateways
import alpha.component as alpha_component
import beta.component as beta_component
import tesser.errors as errors


class Spec(ts.Spec):

    def __init__(self, alpha: alpha_component.Config, beta: beta_component.Config) -> None:
        self.alpha = alpha
        self.beta = beta


class AppConfig(ts.Config):

    def __init__(self, spec: Spec) -> None:
        self.alpha = spec.alpha
        self.beta = spec.beta


class MinimalApp(ts.App):

    def __init__(self, app_config: AppConfig) -> None:
        beta = beta_component.Beta(app_config.beta)
        try:
            alpha = alpha_component.Alpha(app_config.alpha, alpha_gateways.BetaCheckGateway(beta.client))
        except Exception:
            beta.close()
            raise
        self.beta = beta
        self.alpha = alpha

    def close(self) -> None:
        self.alpha.close()
        self.beta.close()


class AppConfigRepository(ts.ConfigRepository, typing.Protocol):

    def get(self) -> AppConfig: ...


class EnvConfigRepository(AppConfigRepository):

    def __init__(self, environ: collections_abc.Mapping[str, str]) -> None:
        self._environ = environ

    def get(self) -> AppConfig:
        storage = self._environ.get("ALPHA_STORAGE")
        if storage is None:
            raise errors.invalid("missing_env", "ALPHA_STORAGE is required")
        engine_url = self._environ.get("RESTATE_URL")
        if engine_url is None:
            raise errors.invalid("missing_env", "RESTATE_URL is required")
        key = self._environ.get("BETA_KEY")
        if key is None:
            raise errors.invalid("missing_env", "BETA_KEY is required")
        return AppConfig(
            Spec(
                alpha=alpha_component.Config(alpha_component.Spec(storage=storage, engine_url=engine_url)),
                beta=beta_component.Config(beta_component.Spec(key=key)),
            )
        )


class AppLoader(ts.Loader):

    def __init__(self, app_config_repository: AppConfigRepository) -> None:
        self._app_config_repository = app_config_repository

    def load(self) -> MinimalApp:
        return MinimalApp(self._app_config_repository.get())


@ts.load
def load() -> MinimalApp:
    return AppLoader(EnvConfigRepository(os.environ)).load()
