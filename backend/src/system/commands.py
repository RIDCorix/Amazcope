import asyncio

from pydantic import BaseModel, Field

from pydantic_commands import command
from system.checks import CheckResult
from system.registries import dependency_registry


class TestDependenciesArgs(BaseModel):
    """Arguments for testing dependencies."""

    test_names: list[str] = Field(
        default_factory=list, description="Specific tests to run (default: all tests)"
    )
    timeout: int = Field(default=30, ge=1, le=300, description="Timeout in seconds for each test")
    verbose: bool = Field(default=False, description="Show detailed output")


@command(
    name="test-dependencies",
    help="Test connectivity to external dependencies",
    arguments=TestDependenciesArgs,
)
def test_dependencies(args: TestDependenciesArgs) -> None:
    """Test connectivity to external dependencies like Redis, database, email server, etc."""

    async def _test_dependencies() -> None:
        # Get tests to run
        if args.test_names:
            tests = []
            for name in args.test_names:
                test = dependency_registry.get(name)
                if test:
                    tests.append(test)
                else:
                    print(f"⚠️  Warning: Test '{name}' not found")
        else:
            tests = list(dependency_registry.registry.keys())

        if not tests:
            print("❌ No tests to run")
            return

        print("🔍 Testing Dependencies\n" + "=" * 50)

        results = []

        for test_name in tests:
            print(f"📋 Testing {test_name}...", end=" ", flush=True)

            test = dependency_registry.get(test_name)()

            try:
                # Run test with timeout
                result = await asyncio.wait_for(test.test(), timeout=args.timeout)
                results.append(result)

                # Print immediate status
                if result.status == "success":
                    print("✅")
                elif result.status == "warning":
                    print("⚠️")
                else:
                    print("❌")

            except TimeoutError:
                result = CheckResult(
                    name=test.name,
                    status="error",
                    message=f"Test timed out after {args.timeout} seconds",
                    details={"timeout": args.timeout},
                    duration_ms=args.timeout * 1000,
                )
                results.append(result)
                print("❌ (timeout)")

            except Exception as e:
                import traceback

                tb_str = traceback.format_exc()
                print("\n----- STACK TRACE -----")
                print(tb_str)
                print("----------------------")
                result = CheckResult(
                    name=test.name,
                    status="error",
                    message=f"Test failed with exception: {str(e)}",
                    details={
                        "error_type": type(e).__name__,
                        "stack_trace": tb_str,
                    },
                    duration_ms=0,
                )
                results.append(result)
                print("❌ (exception)")

        # Print summary
        print("\n" + "=" * 50)
        print("📊 Summary:")

        success_count = sum(1 for r in results if r.status == "success")
        warning_count = sum(1 for r in results if r.status == "warning")
        error_count = sum(1 for r in results if r.status == "error")

        print(f"   ✅ Successful: {success_count}")
        print(f"   ⚠️  Warnings: {warning_count}")
        print(f"   ❌ Errors: {error_count}")
        print(f"   📈 Total: {len(results)}")

        # Print detailed results if verbose or if there are issues
        if args.verbose or warning_count > 0 or error_count > 0:
            print("\n" + "=" * 50)
            print("📋 Detailed Results:")

            for result in results:
                icon = (
                    "✅"
                    if result.status == "success"
                    else "⚠️"
                    if result.status == "warning"
                    else "❌"
                )
                print(f"\n{icon} {result.name.upper()}")
                print(f"   Status: {result.status}")
                print(f"   Message: {result.message}")
                print(f"   Duration: {result.duration_ms:.2f}ms")

                if args.verbose and result.details:
                    print("   Details:")
                    for key, value in result.details.items():
                        print(f"     {key}: {value}")

        # Exit with appropriate code
        if error_count > 0:
            print(f"\n❌ {error_count} dependencies failed")
            exit(1)
        elif warning_count > 0:
            print(f"\n⚠️  {warning_count} dependencies have warnings")
            exit(0)
        else:
            print(f"\n✅ All {success_count} dependencies are healthy")
            exit(0)

    # Run async function
    asyncio.run(_test_dependencies())


# Example usage in other modules:
#
# from commands.health import dependency_registry, BaseCheck, CheckResult
#
# class CustomServiceTest(BaseCheck):
#     @property
#     def name(self) -> str:
#         return "custom_service"
#
#     async def test(self) -> CheckResult:
#         # Your test logic here
#         pass
#
# # Register the test
# dependency_registry.register(CustomServiceTest())


@command(
    name="erd",
    help="Generate and display the Entity-Relationship Diagram (ERD) of the database schema using eralchemy",
)
def erd_command(args: None) -> None:
    # run eralchemy to generate ERD
    import subprocess

    from core.config import settings

    subprocess.run(["eralchemy", "-i", settings.SYNC_DATABASE_URL, "-o", "erd.dot"])
