# workspace/

本目录统一存放**程序运行过程中生成的本地数据**，例如未来的：

```text
runs/
wiki/
reports/
cache/
```

规则：

> Runtime output only goes to `workspace/`.

运行产物**默认不提交 Git**（见根目录 `.gitignore`）。
保留本 README 仅用于维持目录边界。
