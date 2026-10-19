"""Fixed standalone entrypoint; currently always denies before scientific import."""

from aluclu.alc_r0.fixed_d_worker import main


if __name__ == "__main__":
    raise SystemExit(main())
