# Публикация Velune

Рекомендуемое имя репозитория: **Velune**. Описание для поля Description находится в [repository-description.txt](repository-description.txt).

1. Создай пустой репозиторий на GitHub. Не добавляй стандартную лицензию: проект уже содержит собственную `LICENSE`.
2. Загрузить исходники можно из `dist/Velune-source.zip`: распакуй архив и загрузи его содержимое, включая `.github`, `.gitignore` и `.gitattributes`. Сам архив в репозиторий добавлять не нужно.
3. Альтернативный вариант — Git из корня проекта:

```powershell
git init -b main
git add .
git commit -m "Initial Velune release"
git remote add origin https://github.com/WolderFin/Velune.git
git push -u origin main
```

Адрес выше — пример для рекомендованного имени; используй адрес созданного репозитория.

4. Проверь результат Windows workflow во вкладке Actions.
5. Создай релиз с тегом `v1.0.0` и приложи **Velune-windows-x64.zip** из `dist/` или артефактов Actions. Весь архив необходим для сохранения сторонних лицензий и исходников LGPL-компонента.

Для обновления архива исходников после правок:

```powershell
.\.venv\Scripts\python.exe scripts/package_source.py
```

`dist`, локальное окружение, кэш и служебные папки исключены через `.gitignore`.
