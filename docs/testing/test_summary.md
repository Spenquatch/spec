# Test File Summary

## integration/cli/commands/test_init_command_integration.py

### Test Classes
- `TestInitCommandIntegration`: 7 test methods

### Standalone Tests: 7

---

## integration/cli/test_cli_app_integration.py

### Test Classes
- `TestCLIAppIntegration`: 9 test methods

### Standalone Tests: 9

---

## integration/cli/test_context_injection_integration.py

### Test Classes
- `TestContextInjectionIntegration`: 8 test methods
- `TestCrossSliceIntegration`: 2 test methods
- `TestDIMigrationContext`: 2 test methods

### Standalone Tests: 14

---

## integration/test_add_command_migration.py

### Test Classes
- `TestAddCommandMigrationIntegration`: 3 test methods
- `TestCrossSliceContextIntegration`: 2 test methods
- `TestAddCommandDecoratorCompatibility`: 2 test methods

### Standalone Tests: 7

---

## integration/test_ai_context_pipeline_ai_004.py

### Test Classes
- `TestAIContextPipelineEndToEnd`: 8 test methods
- `TestAIContextPipelineErrorRecovery`: 3 test methods

### Standalone Tests: 11

---

## integration/test_commit_command_migration.py

### Test Classes
- `TestCommitCommandMigrationIntegration`: 8 test methods

### Standalone Tests: 8

---

## integration/test_context_based_fixture_migration.py

### Test Classes
- `TestContextBasedFixtureMigration`: 6 test methods

### Standalone Tests: 6

---

## integration/test_gen_command_migration.py

### Test Classes
- `TestGenCommandMigrationIntegration`: 8 test methods

### Standalone Tests: 8

---

## integration/test_git_workflows.py

### Test Classes
- `TestGitWorkflowIntegration`: 7 test methods
- `TestGitPathIntegration`: 3 test methods

### Standalone Tests: 10

---

## integration/test_migration_cleanup_and_validation.py

### Test Classes
- `TestMigrationCleanupIntegration`: 3 test methods

### Standalone Tests: 3

---

## integration/test_pre_commit_hook_integration.py

### Test Classes
- `TestPreCommitHookIntegration`: 1 test methods
- `TestHookIntegrationWithDetectionSystem`: 2 test methods
- `TestHookIntegrationDIMigrationContext`: 2 test methods
- `TestCrossSliceIntegration`: 1 test methods

### Standalone Tests: 6

---

## integration/test_singleton_detection_system.py

### Test Classes
- `TestSingletonDetectionSystemIntegration`: 5 test methods

### Standalone Tests: 5

---

## integration/test_singleton_infrastructure_removal.py

### Test Classes
- `TestSingletonInfrastructureRemoval`: 5 test methods

### Standalone Tests: 5

---

## integration/test_test_fixture_analysis.py

### Test Classes
- `TestTestFixtureAnalysisIntegration`: 5 test methods

### Standalone Tests: 5

---

## integration/utils/test_command_analysis_integration.py

### Test Classes
- `TestCommandAnalysisIntegration`: 4 test methods

### Standalone Tests: 4

---

## unit/ai/analysis/test_sanitizer_ai_001.py

### Test Classes
- `TestCodeSanitizerInit`: 3 test methods
- `TestCodeSanitizerSanitize`: 9 test methods
- `TestCodeSanitizerValidateContent`: 5 test methods
- `TestCodeSanitizerApplySecurityPatterns`: 4 test methods
- `TestCodeSanitizerCompilePatterns`: 3 test methods
- `TestCodeSanitizerFileAllowed`: 5 test methods
- `TestCodeSanitizerValidateFileSecurity`: 5 test methods
- `TestCodeSanitizerSanitizationSummary`: 2 test methods
- `TestCodeSanitizerSecurityPatterns`: 8 test methods
- `TestCodeSanitizerMaliciousCodeDetection`: 5 test methods
- `TestCodeSanitizerIntegration`: 5 test methods

### Standalone Tests: 54

---

## unit/ai/context/test_embeddings_ai_002.py

### Test Classes
- `TestEmbeddingGenerator`: 16 test methods
- `TestGenerateEmbeddingsFunction`: 5 test methods
- `TestEmbeddingGeneratorIntegration`: 4 test methods

### Standalone Tests: 25

---

## unit/ai/context/test_ranking_ai_003.py

### Test Classes
- `TestRelevanceRankerInitialization`: 5 test methods
- `TestRankContexts`: 7 test methods
- `TestScoringMethods`: 22 test methods
- `TestGetRankingSummary`: 4 test methods
- `TestEdgeCasesAndErrorHandling`: 5 test methods
- `TestIntegrationScenarios`: 3 test methods

### Standalone Tests: 46

---

## unit/ai/monitoring/test_ai_monitoring_infrastructure_001.py

### Test Classes
- `TestAIMonitoringInfrastructure`: 27 test methods
- `TestAIMonitoringIntegrationScenarios`: 5 test methods

### Standalone Tests: 32

---

## unit/ai/providers/test_generation_ai_001.py

### Test Classes
- `TestDocumentationGeneratorInitialization`: 2 test methods
- `TestDocumentationGeneratorModelLoading`: 5 test methods
- `TestDocumentationGeneratorContentGeneration`: 5 test methods
- `TestDocumentationGeneratorPromptCreation`: 4 test methods
- `TestDocumentationGeneratorTemplateValidation`: 4 test methods
- `TestDocumentationGeneratorUtilityMethods`: 16 test methods
- `TestDocumentationGeneratorModelKwargs`: 5 test methods
- `TestDocumentationGeneratorTextGeneration`: 4 test methods
- `TestDocumentationGeneratorParseContent`: 3 test methods

### Standalone Tests: 48

---

## unit/ai/providers/test_generation_ai_providers_002.py

### Test Classes
- `TestDocumentationGeneratorInitialization`: 2 test methods
- `TestDocumentationGeneratorModelLoading`: 5 test methods
- `TestDocumentationGeneratorGeneration`: 5 test methods
- `TestDocumentationGeneratorPromptCreation`: 3 test methods
- `TestDocumentationGeneratorModelGeneration`: 3 test methods
- `TestDocumentationGeneratorUtilityMethods`: 15 test methods
- `TestDocumentationGeneratorEdgeCases`: 6 test methods
- `TestDocumentationGeneratorPerformance`: 2 test methods
- `TestDocumentationGeneratorIntegration`: 1 test methods

### Standalone Tests: 42

---

## unit/ai/providers/test_llamacpp_ai_001_micro.py

### Test Classes
- `TestLlamaCppProviderCrossPlatformBehavior`: 5 test methods
- `TestLlamaCppProviderAdvancedPromptGeneration`: 5 test methods
- `TestLlamaCppProviderValidationEdgeCases`: 6 test methods
- `TestLlamaCppProviderConfigurationValidation`: 3 test methods
- `TestLlamaCppProviderContentParsing`: 5 test methods
- `TestLlamaCppProviderErrorRecovery`: 4 test methods
- `TestLlamaCppProviderContractCompliance`: 4 test methods
- `TestLlamaCppProviderIntegrationValidation`: 3 test methods
- `TestLlamaCppProviderQualityValidation`: 5 test methods

### Standalone Tests: 40

---

## unit/ai/providers/test_llamacpp_ai_002.py

### Test Classes
- `TestLlamaCppProviderInitialization`: 6 test methods
- `TestLlamaCppProviderAvailability`: 4 test methods
- `TestLlamaCppProviderModelLoading`: 4 test methods
- `TestLlamaCppProviderTextGeneration`: 12 test methods
- `TestLlamaCppProviderUtilityMethods`: 8 test methods
- `TestLlamaCppProviderInfoAndLogging`: 4 test methods
- `TestLlamaCppProviderIntegrationWithHelpers`: 4 test methods
- `TestLlamaCppProviderErrorScenarios`: 4 test methods
- `TestLlamaCppProviderQualityGates`: 4 test methods

### Standalone Tests: 50

---

## unit/ai/providers/test_manager_ai_003.py

### Test Classes
- `TestCreateWorkflowResult`: 5 test methods
- `TestProviderManager`: 15 test methods
- `TestProviderManagerEdgeCases`: 3 test methods
- `TestProviderManagerIntegrationWithMockDoubles`: 3 test methods

### Standalone Tests: 26

---

## unit/cli/commands/test_add_command_execute_micro_004.py

### Test Classes
- `TestAddCommandExecuteMicro004`: 10 test methods

### Standalone Tests: 10

---

## unit/cli/commands/test_add_migration.py

### Test Classes
- `TestAddCommandMigration`: 9 test methods
- `TestAddCommandContextUsage`: 2 test methods
- `TestAddCommandErrorHandling`: 3 test methods

### Standalone Tests: 14

---

## unit/cli/test_app_context_setup.py

### Test Classes
- `TestCLIAppContextSetup`: 8 test methods
- `TestCreateCLIApp`: 3 test methods

### Standalone Tests: 11

---

## unit/cli/test_cli_app_micro_001.py

### Test Classes
- `TestCLIAppMicro001`: 17 test methods

### Standalone Tests: 17

---

## unit/cli/test_cli_integration_micro_001.py

### Test Classes
- `TestCLIIntegrationMicro001`: 6 test methods

### Standalone Tests: 6

---

## unit/cli/test_cli_utils_micro_001.py

### Test Classes
- `TestCLIUtilsMicro001`: 25 test methods

### Standalone Tests: 27

---

## unit/cli/test_decorators.py

### Test Classes
- `TestContextInjectionDecorator`: 7 test methods
- `TestInjectContextParametricDecorator`: 4 test methods
- `TestWithContextAlias`: 2 test methods
- `TestGetSpecContextFromClick`: 6 test methods
- `TestContextInjectionError`: 2 test methods

### Standalone Tests: 23

---

## unit/config/test_loader_integration_config_002.py

### Test Classes
- `TestConfigurationLoaderIntegration`: 21 test methods

### Standalone Tests: 21

---

## unit/config/test_validation.py

### Test Classes
- `TestConfigurationValidator`: 39 test methods

### Standalone Tests: 39

---

## unit/core/test_commit_manager_validation_micro_001.py

### Test Classes
- `TestSpecCommitManagerValidation`: 7 test methods
- `TestSpecCommitManagerAddFiles`: 6 test methods
- `TestSpecCommitManagerCommitChanges`: 9 test methods
- `TestSpecCommitManagerErrorHandling`: 6 test methods
- `TestSpecCommitManagerMessageAndHashUtilities`: 7 test methods
- `TestSpecCommitManagerIntegration`: 3 test methods

### Standalone Tests: 38

---

## unit/core/test_commit_manager_workflow_002.py

### Test Classes
- `TestSpecCommitManagerInitialization`: 3 test methods
- `TestSpecCommitManagerAddFiles`: 10 test methods
- `TestSpecCommitManagerCommitChanges`: 8 test methods
- `TestSpecCommitManagerCreateTag`: 11 test methods
- `TestSpecCommitManagerRollback`: 9 test methods
- `TestSpecCommitManagerStatus`: 4 test methods
- `TestSpecCommitManagerHelperMethods`: 4 test methods
- `TestSpecCommitManagerOperationSummaries`: 7 test methods
- `TestSpecCommitManagerIntegration`: 3 test methods

### Standalone Tests: 59

---

## unit/core/test_workflow_orchestrator.py

### Test Classes
- `TestSpecWorkflowOrchestrator`: 18 test methods
- `TestWorkflowOrchestratorIntegration`: 2 test methods

### Standalone Tests: 20

---

## unit/core/test_workflow_state_transitions_workflow_003.py

### Test Classes
- `TestWorkflowStateTransitions`: 5 test methods
- `TestWorkflowStepTransitions`: 6 test methods
- `TestWorkflowStateStepManagement`: 5 test methods
- `TestWorkflowStateSummary`: 2 test methods
- `TestWorkflowStateManagerTransitions`: 11 test methods
- `TestWorkflowStateManagerStaleCleanup`: 3 test methods
- `TestWorkflowStateWithHelperIntegration`: 3 test methods
- `TestStateTransitionEdgeCases`: 4 test methods

### Standalone Tests: 39

---

## unit/file_processing/test_batch_processor_micro_001.py

### Test Classes
- `TestBatchProcessingOptions`: 4 test methods
- `TestBatchProcessingResult`: 6 test methods
- `TestBatchFileProcessor`: 18 test methods
- `TestConvenienceFunctions`: 2 test methods
- `TestBatchProcessorIntegration`: 1 test methods
- `TestBatchProcessorErrorHandling`: 2 test methods

### Standalone Tests: 33

---

## unit/file_system/test_cross_platform_micro_001.py

### Test Classes
- `TestCrossPlatformPathHandling`: 7 test methods
- `TestPermissionHandling`: 7 test methods
- `TestPathValidationEdgeCases`: 8 test methods

### Standalone Tests: 22

---

## unit/file_system/test_path_resolver_micro_001.py

### Test Classes
- `TestPathResolverMicro001`: 29 test methods

### Standalone Tests: 29

---

## unit/git/test_operations.py

### Test Classes
- `TestGitOperationsInitialization`: 3 test methods
- `TestGitCommandExecution`: 6 test methods
- `TestGitEnvironmentConfiguration`: 5 test methods
- `TestGitRepositoryInitialization`: 4 test methods
- `TestGitAvailabilityChecks`: 6 test methods
- `TestGitOperationsIntegration`: 3 test methods
- `TestGitOperationsEdgeCases`: 4 test methods

### Standalone Tests: 31

---

## unit/git/test_operations_git_001.py

### Test Classes
- `TestGitOperationsInit`: 3 test methods
- `TestGitOperationsEnvironment`: 3 test methods
- `TestGitOperationsCommandPreparation`: 3 test methods
- `TestGitOperationsCommandExecution`: 6 test methods
- `TestGitOperationsRepositoryInit`: 4 test methods
- `TestGitOperationsUtilityMethods`: 5 test methods
- `TestGitOperationsEdgeCases`: 2 test methods

### Standalone Tests: 26

---

## unit/git/test_path_converter_git_003.py

### Test Classes
- `TestGitPathConverterInitialization`: 3 test methods
- `TestConvertToGitPath`: 8 test methods
- `TestConvertFromGitPath`: 6 test methods
- `TestConvertToAbsoluteSpecsPath`: 4 test methods
- `TestIsUnderSpecsDir`: 5 test methods
- `TestNormalizePathSeparators`: 4 test methods
- `TestGetConversionInfo`: 5 test methods
- `TestCrossPlatformBehavior`: 5 test methods
- `TestErrorHandling`: 4 test methods
- `TestIntegrationWithUtilities`: 3 test methods

### Standalone Tests: 47

---

## unit/git/test_repository_git_002.py

### Test Classes
- `TestSpecGitRepositoryInit`: 3 test methods
- `TestSpecGitRepositoryIsolation`: 11 test methods
- `TestSpecGitRepositoryManagement`: 13 test methods
- `TestSpecGitRepositoryFileOperations`: 9 test methods
- `TestSpecGitRepositoryIntegration`: 3 test methods

### Standalone Tests: 39

---

## unit/templates/test_ai_integration_template_001.py

### Test Classes
- `TestAITemplateIntegrator`: 18 test methods
- `TestProcessAIVariables`: 7 test methods
- `TestValidateEnhancement`: 15 test methods
- `TestIntegrationScenarios`: 4 test methods

### Standalone Tests: 44

---

## unit/templates/test_generator_template_002.py

### Test Classes
- `TestSpecContentGenerator`: 11 test methods
- `TestGenerateSpecContent`: 3 test methods
- `TestConvenienceFunction`: 1 test methods
- `TestValidationMethods`: 5 test methods

### Standalone Tests: 20

---

## unit/templates/test_generator_template_002_fixed.py

### Test Classes
- `TestSpecContentGeneratorBasic`: 2 test methods
- `TestPrepareSubstitutionsUnit`: 6 test methods
- `TestWriteContentFileUnit`: 3 test methods
- `TestConvenienceFunctionUnit`: 1 test methods
- `TestGenerateSpecContentIntegration`: 2 test methods
- `TestValidationMethods`: 3 test methods

### Standalone Tests: 17

---

## unit/test_exceptions.py

### Test Classes
- `TestSpecError`: 9 test methods
- `TestSpecNotInitializedError`: 5 test methods
- `TestSpecPermissionError`: 2 test methods
- `TestSpecGitError`: 2 test methods
- `TestSpecConfigurationError`: 2 test methods
- `TestSpecTemplateError`: 2 test methods
- `TestSpecFileError`: 2 test methods
- `TestSpecRepositoryError`: 2 test methods
- `TestSpecWorkflowError`: 2 test methods
- `TestSpecValidationError`: 2 test methods
- `TestSpecConflictError`: 2 test methods
- `TestSpecProcessingError`: 2 test methods
- `TestSpecBatchProcessingError`: 2 test methods
- `TestSpecGenerationError`: 2 test methods
- `TestCreateSpecError`: 6 test methods
- `TestExceptionIntegration`: 6 test methods

### Standalone Tests: 50

---

## unit/ui/test_console_ui_002.py

### Test Classes
- `TestSpecConsole`: 16 test methods
- `TestConsoleManager`: 4 test methods
- `TestGlobalConsoleFunctions`: 4 test methods

### Standalone Tests: 24

---

## unit/ui/test_error_display.py

### Test Classes
- `TestErrorPanel`: 18 test methods
- `TestDiagnosticDisplay`: 7 test methods
- `TestStackTraceFormatter`: 5 test methods
- `TestUtilityFunctions`: 18 test methods
- `TestErrorHandling`: 5 test methods

### Standalone Tests: 53

---

## unit/ui/test_progress_manager_ui_001.py

### Test Classes
- `TestProgressState`: 4 test methods
- `TestProgressManagerInitialization`: 3 test methods
- `TestProgressManagerEventHandling`: 4 test methods
- `TestProgressManagerOperations`: 5 test methods
- `TestProgressManagerEventHandlers`: 4 test methods
- `TestProgressManagerSingleton`: 5 test methods
- `TestConvenienceFunctions`: 2 test methods
- `TestProgressManagerPrivateMethods`: 4 test methods

### Standalone Tests: 31

---

## unit/utils/assessment/test_readiness_evaluator.py

### Test Classes
- `TestAssessMigrationReadiness`: 4 test methods
- `TestStabilityScoreCalculation`: 3 test methods
- `TestDeliverableCompletenessEvaluation`: 3 test methods
- `TestOverallReadinessCalculation`: 3 test methods
- `TestRecommendationGeneration`: 2 test methods
- `TestRiskFactorIdentification`: 2 test methods
- `TestMigrationBlockerIdentification`: 3 test methods
- `TestReadinessAssessmentError`: 2 test methods

### Standalone Tests: 22

---

## unit/utils/test_cleanup_utils.py

### Test Classes
- `TestSafeFileRemoval`: 5 test methods
- `TestValidateNoReferences`: 6 test methods
- `TestCleanupSingletonInfrastructure`: 3 test methods
- `TestCleanupCompatibilityLayer`: 3 test methods
- `TestCleanupUtilsIntegration`: 2 test methods

### Standalone Tests: 19

---

## unit/utils/test_cli_setup_utils.py

### Test Classes
- `TestInitializeCLIContext`: 4 test methods
- `TestSetupClickContextStorage`: 4 test methods
- `TestCreateCLIAppWithContext`: 4 test methods
- `TestValidateCLIContextSetup`: 4 test methods

### Standalone Tests: 16

---

## unit/utils/test_command_analysis.py

### Test Classes
- `TestCommandAnalysis`: 7 test methods
- `TestCommandAnalysisHelpers`: 3 test methods
- `TestCommandAnalysisErrorHandling`: 2 test methods
- `TestCrossPlatformSupport`: 1 test methods
- `TestIntegrationWithExistingCode`: 1 test methods

### Standalone Tests: 14

---

## unit/utils/test_context_utils.py

### Test Classes
- `TestValidateContextImmutability`: 5 test methods
- `TestCreateContextHash`: 8 test methods

### Standalone Tests: 13

---

## unit/utils/test_decorator_utils.py

### Test Classes
- `TestCreateContextInjector`: 9 test methods
- `TestPreserveFunctionMetadata`: 6 test methods
- `TestValidateDecoratorTarget`: 7 test methods
- `TestDecoratorError`: 3 test methods

### Standalone Tests: 27

---

## unit/utils/test_factory_utils.py

### Test Classes
- `TestDetectEnvironmentType`: 7 test methods
- `TestValidateFactoryInputs`: 13 test methods

### Standalone Tests: 20

---

## unit/utils/test_helpers/test_ai_test_doubles.py

### Test Classes
- `TestMockLlamaCppProvider`: 14 test methods
- `TestMockGenerationProvider`: 10 test methods
- `TestAIResponseFixtures`: 13 test methods
- `TestAITimeoutSimulator`: 4 test methods
- `TestMockHuggingFaceModel`: 4 test methods
- `TestFactoryFunctions`: 6 test methods
- `TestPatchDecorators`: 5 test methods
- `TestPytestFixtures`: 5 test methods
- `TestIntegrationScenarios`: 4 test methods

### Standalone Tests: 65

---

## unit/utils/test_helpers/test_cli_test_helpers.py

### Test Classes
- `TestCLICommandRunner`: 12 test methods
- `TestCLITestResult`: 12 test methods
- `TestCLIOutputCapture`: 7 test methods
- `TestUserInputMocker`: 10 test methods
- `TestFactoryFunctions`: 5 test methods
- `TestIsolatedCLIEnvironment`: 3 test methods
- `TestErrorHandling`: 4 test methods

### Standalone Tests: 56

---

## unit/utils/test_helpers/test_file_system_test_helpers.py

### Test Classes
- `TestTempFileStructureBuilder`: 16 test methods
- `TestFilePermissionMocker`: 12 test methods
- `TestCrossPlatformPathValidator`: 11 test methods
- `TestFactoryFunctions`: 3 test methods
- `TestIntegrationScenarios`: 2 test methods

### Standalone Tests: 44

---

## unit/utils/test_helpers/test_git_test_helpers.py

### Test Classes
- `TestGitRepositoryMocker`: 40 test methods
- `TestGitCommandSimulator`: 13 test methods
- `TestGitEnvironmentIsolator`: 6 test methods
- `TestFactoryFunctions`: 4 test methods
- `TestIntegrationScenarios`: 4 test methods
- `TestCoverageEdgeCases`: 7 test methods

### Standalone Tests: 74

---

## unit/utils/test_helpers/test_template_test_helpers.py

### Test Classes
- `TestTemplateFixture`: 3 test methods
- `TestTemplateFixtureGenerator`: 11 test methods
- `TestVariableSubstitutionMocker`: 7 test methods
- `TestAITemplateMocker`: 8 test methods
- `TestTemplateFixtures`: 3 test methods
- `TestTemplateTestHelperFixtures`: 5 test methods

### Standalone Tests: 37

---

## unit/utils/test_helpers/test_test_failure_categorizer.py

### Test Classes
- `TestCategorizeTestFailure`: 6 test methods
- `TestAnalyzeFailureType`: 8 test methods
- `TestDetermineFailurePriority`: 6 test methods
- `TestGenerateRemediationNotes`: 4 test methods
- `TestGetRemediationStrategy`: 1 test methods
- `TestEstimateRemediationEffort`: 1 test methods
- `TestDataClasses`: 2 test methods
- `TestEnumDefinitions`: 2 test methods

### Standalone Tests: 30

---

## unit/utils/test_helpers/test_workflow_test_helpers.py

### Test Classes
- `TestWorkflowStateBuilder`: 14 test methods
- `TestStateTransitionMocker`: 10 test methods
- `TestBackupRollbackFixtures`: 10 test methods
- `TestWorkflowErrorSimulator`: 13 test methods
- `TestFactoryFunctions`: 4 test methods
- `TestPytestFixtures`: 7 test methods
- `TestIntegrationScenarios`: 3 test methods

### Standalone Tests: 61

---

## unit/utils/test_migration_utils.py

### Test Classes
- `TestMigrationUtils`: 21 test methods

### Standalone Tests: 21

---

## unit/utils/test_path_utils_micro_001.py

### Test Classes
- `TestSafeRelativeTo`: 6 test methods
- `TestEnsureDirectory`: 6 test methods
- `TestNormalizePath`: 5 test methods
- `TestResolveProjectRoot`: 6 test methods
- `TestIsSubpath`: 4 test methods
- `TestGetRelativePathOrAbsolute`: 4 test methods
- `TestEnsurePathPermissions`: 6 test methods
- `TestCrossPlatformUtilities`: 16 test methods

### Standalone Tests: 53

---

## unit/utils/test_path_utils_path_001.py

### Test Classes
- `TestSafeRelativeTo`: 7 test methods
- `TestEnsureDirectory`: 7 test methods
- `TestNormalizePath`: 7 test methods
- `TestResolveProjectRoot`: 8 test methods
- `TestIsSubpath`: 6 test methods
- `TestGetRelativePathOrAbsolute`: 5 test methods
- `TestEnsurePathPermissions`: 7 test methods
- `TestNormalizePathSeparators`: 6 test methods
- `TestRemoveSpecsPrefix`: 6 test methods
- `TestEnsureSpecsPrefix`: 6 test methods
- `TestIsSpecsPath`: 7 test methods
- `TestConvertToPosixStyle`: 4 test methods
- `TestCrossPlatformIntegration`: 5 test methods

### Standalone Tests: 81

---

## unit/utils/test_security_validators_001.py

### Test Classes
- `TestSecurityValidatorsInputValidation`: 36 test methods
- `TestSecurityValidatorsPrivateFunctions`: 3 test methods

### Standalone Tests: 39

---

## unit/utils/test_test_analysis.py

### Test Classes
- `TestAnalyzeTestFixtures`: 7 test methods
- `TestIdentifySingletonDependencies`: 5 test methods
- `TestFixtureInfo`: 1 test methods
- `TestFixtureAnalysisReport`: 1 test methods

### Standalone Tests: 14

---

## unit/validation/test_import_validator.py

### Test Classes
- `TestImportViolation`: 2 test methods
- `TestExtractImportNodes`: 5 test methods
- `TestExtractFromImportNodes`: 4 test methods
- `TestImportValidator`: 6 test methods

### Standalone Tests: 17

---
