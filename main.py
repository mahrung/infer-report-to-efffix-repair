from algorithm.run_efffix import run_effix
from algorithm.utils.parse_arguments import parse_arguments
from algorithm.utils.get_target_container import get_target_container


def main():
    args = parse_arguments()

    target_container, project, case, start_new, should_exit = get_target_container(args)
    if should_exit:
        return

    run_effix(
        target_container,
        project=project,
        case=case,
        start_new=start_new,
        repair_only=args.repair_only,
        generate_config=args.generate_config
    )


if __name__ == "__main__":
    main()
