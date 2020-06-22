# clang-tidy checks
## Warning is not useful
If you found that a warning produced by clang-tidy is not useful:
  
- If clang-tidy must not run for some files at all (e.g. lit test), please
[add files to ignorelist](../scripts/clang-tidy.ignore).

- Consider fixing or [suppressing diagnostic](https://clang.llvm.org/extra/clang-tidy/#suppressing-undesired-diagnostics)
  if there is a good reason.
  
- [File a bug](https://github.com/google/llvm-premerge-checks/issues/new?assignees=&labels=bug&template=bug_report.md&title=)
  if build process should be improved. 

- If you believe that you found a clang-tidy bug then please keep in mind that clang-tidy version run by bot
  might not be most recent. Please reproduce your issue on current version before submitting a bug to clang-tidy.

## Review comments

Build bot leaves inline comments only for a small subset of files that are not blacklisted for analysis (see above) *and*
specifically whitelisted for comments.

That is done to avoid potential noise when a file already contains a number of warnings.

If your are confident that some files are in good shape already, please
[whitelist them](../scripts/clang-tidy-comments.ignore).

----

[about pre-merge checks](docs/user_doc.md)
