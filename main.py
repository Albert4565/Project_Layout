import os
import matplotlib.pyplot as plt
from layout import qwerty_layout, dictor_layout, vizov_layout
import numpy as np

left_hand = {'f5l', 'f4l', 'f3l', 'f2l', 'f1l'}
right_hand = {'f1r', 'f2r', 'f3r', 'f4r', 'f5r'}


def calculate_fines(pos1, pos2):
    """
    Вычисляем штраф пальца за перемещение между позициями

    Args:
        pos1: прошлая позиция пальца
        pos2: текущая позиция пальца

    Returns:
        Штрафной балл за перемещение
    """

    if pos1 is None or pos2 is None:
        return 0

    if pos1 == pos2:
        return 0

    row1, col1 = pos1
    row2, col2 = pos2

    row_diff = abs(row1 - row2)
    col_diff = abs(col1 - col2)

    fine = row_diff + col_diff

    return fine


def analyze_text(text, layout_config):
    """
    Анализирует текст, вычисляет штраф за перемещение пальцев и
    обрабатывает обычные символы, пробелы, shift, enter, alt

    Args:
        text: текст для анализа
        layout_config: данные расладки

    Returns:
        Cуммарный штраф, штрафы по каждому пальцу, общее количество обработанных символов
    """

    layout = layout_config['layout']
    home_positions = layout_config['home_positions']
    finger_assignment = layout_config['finger_assignment']

    finger_penalties = {f: 0 for f in home_positions}
    current_positions = home_positions.copy()
    previous_finger = None
    total_penalty = 0
    total_chars = 0

    for char in text:
        if char not in layout and char != ' ' and char != '\n' and not (char.isupper() or char in '!@"№;%:?*()_+'):
            continue

        if char == ' ':
            current_finger = 'f1l'
            finger_penalties[current_finger] += 1
            total_penalty += 1
            total_chars += 1

            if previous_finger and current_finger:
                current_hand = 'left' if current_finger in left_hand else 'right'
                previous_hand = 'left' if previous_finger in left_hand else 'right'
                if current_hand != previous_hand:
                    finger_penalties[current_finger] += 1
                    total_penalty += 1

            previous_finger = current_finger

        elif char.isupper() or char in '!@"№;%:?*()_+':
            lower_char = char.lower()
            if lower_char not in layout:
                continue

            if previous_finger and previous_finger in right_hand:
                shift_finger = 'f5r'
            else:
                shift_finger = 'f5l'

            letter_finger = finger_assignment.get(char.lower(), 'f1l')

            finger_penalties[shift_finger] += 1
            total_penalty += 1

            if previous_finger and shift_finger:
                current_hand = 'left' if shift_finger in left_hand else 'right'
                previous_hand = 'left' if previous_finger in left_hand else 'right'
                if current_hand != previous_hand:
                    finger_penalties[shift_finger] += 1
                    total_penalty += 1

            if shift_finger and letter_finger:
                current_hand = 'left' if letter_finger in left_hand else 'right'
                previous_hand = 'left' if shift_finger in left_hand else 'right'
                if current_hand != previous_hand:
                    finger_penalties[letter_finger] += 1
                    total_penalty += 1

            current_pos = layout[char.lower()]
            movement_penalty = calculate_fines(current_positions[letter_finger], current_pos)
            finger_penalties[letter_finger] += movement_penalty
            total_penalty += movement_penalty

            current_positions[letter_finger] = current_pos
            previous_finger = letter_finger
            total_chars += 2

        elif layout_config['name'] == 'Вызов' and char in layout_config.get('alt_symbols', set()):
            alt_finger = 'f1r'

            letter_finger = finger_assignment.get(char, 'f1l')

            finger_penalties[alt_finger] += 1
            total_penalty += 1

            if previous_finger and alt_finger:
                current_hand = 'right'
                previous_hand = 'left' if previous_finger in left_hand else 'right'
                if current_hand != previous_hand:
                    finger_penalties[alt_finger] += 1
                    total_penalty += 1

            if letter_finger:
                letter_hand = 'left' if letter_finger in left_hand else 'right'
                if letter_hand != 'right':
                    finger_penalties[letter_finger] += 1
                    total_penalty += 1

            current_pos = layout[char]
            movement_penalty = calculate_fines(current_positions[letter_finger], current_pos)
            finger_penalties[letter_finger] += movement_penalty
            total_penalty += movement_penalty
            current_positions[letter_finger] = current_pos

            previous_finger = letter_finger
            total_chars += 2

        elif char == '\n':
            current_finger = 'f5r'
            finger_penalties[current_finger] += 2
            total_penalty += 2
            total_chars += 1

            if previous_finger and current_finger:
                current_hand = 'left' if current_finger in left_hand else 'right'
                previous_hand = 'left' if previous_finger in left_hand else 'right'
                if current_hand != previous_hand:
                    finger_penalties[current_finger] += 1
                    total_penalty += 1

            previous_finger = current_finger

        elif char in layout:
            current_finger = finger_assignment.get(char, 'f1l')
            current_pos = layout[char]

            movement_penalty = calculate_fines(current_positions[current_finger], current_pos)
            finger_penalties[current_finger] += movement_penalty
            total_penalty += movement_penalty

            current_positions[current_finger] = current_pos
            total_chars += 1

            if previous_finger and current_finger:
                current_hand = 'left' if current_finger in left_hand else 'right'
                previous_hand = 'left' if previous_finger in left_hand else 'right'
                if current_hand != previous_hand:
                    finger_penalties[current_finger] += 1
                    total_penalty += 1

            previous_finger = current_finger

    return total_penalty, finger_penalties, total_chars


def analyze_file(filename, layout_config, chunk_size=1024 * 1024):
    """
    Анализ файлов целиком, используя заданную раскладку

    Args:
        filename: путь к файлу
        layout_config: данные раскладки
        chunk_size: размер части для чтения больших файлов (1мб)

    Returns:
        сумма штрафов, штраф по каждому пальцу, общее количество символов
        (в случае ошибок - 0 и {})
    """
    try:
        file_size = os.path.getsize(filename)
        print(f"Анализ файла: {filename} ({file_size / 1024 / 1024:.2f} МБ)")

        total_penalty = 0
        total_chars = 0
        finger_penalties = {f: 0 for f in layout_config['home_positions']}

        with open(filename, 'r', encoding='utf-8') as file:
            if file_size <= 10 * 1024 * 1024:
                text = file.read()
                return analyze_text(text, layout_config)
            else:
                print("Файл большой, читаем по частям...")
                while True:
                    chunk = file.read(chunk_size)
                    if not chunk:
                        break

                    penalty, stats, chars = analyze_text(chunk, layout_config)
                    total_penalty += penalty
                    total_chars += chars

                    for finger in finger_penalties:
                        finger_penalties[finger] += stats[finger]

        return total_penalty, finger_penalties, total_chars

    except FileNotFoundError:
        print(f"Файл {filename} не найден")
        return 0, {}, 0
    except Exception as e:
        print(f"Ошибка при обработке файла: {e}")
        return 0, {}, 0


def calculate_hand_penalties(finger_penalties):
    """
    Суммирует отдельно штрафы по пальцам левой и провой рук

    Args:
        finger_penalties: штрафы по пальцам

    Returns:
        Штрафы левой руки и правой
    """
    left_penalty = sum(finger_penalties[f] for f in left_hand if f in finger_penalties)
    right_penalty = sum(finger_penalties[f] for f in right_hand if f in finger_penalties)
    return left_penalty, right_penalty


def plot_finger_penalties_comparison(all_results, filename):
    """
    Строим общую диаграмму штрафов по пальцам для всех раскладок на одном графике

    Args:
        all_results: список кортежей (название раскладки, штрафы по пальцам)
        filename: имя анализируемого файла

    Returns:
        None
    """

    finger_order = ['f5l', 'f4l', 'f3l', 'f2l', 'f1l', 'f1r', 'f2r', 'f3r', 'f4r', 'f5r']

    finger_names_ru = {
        'f5l': 'Левый\n мизинец',
        'f4l': 'Левый\n безымянный',
        'f3l': 'Левый\n средний',
        'f2l': 'Левый\n указательный',
        'f1l': 'Левый\n большой',
        'f1r': 'Правый\n большой',
        'f2r': 'Правый\n указательный',
        'f3r': 'Правый\n средний',
        'f4r': 'Правый\n безымянный',
        'f5r': 'Правый\n мизинец'
    }

    labels = [finger_names_ru[f] for f in finger_order]

    colors = ['red', 'black', 'purple']

    plt.figure(figsize=(14, 10))

    bar_width = 0.25
    y_pos = np.arange(len(labels))

    for i, (layout_name, finger_penalties) in enumerate(all_results):
        penalties = [finger_penalties[f] for f in finger_order]
        total_penalty = sum(penalties)

        display_name = {
            'Йцукен': 'Йцукен',
            'Диктор': 'Диктор',
            'Вызов': 'Вызов'
        }.get(layout_name, layout_name)

        positions = y_pos + i * bar_width
        plt.barh(positions, penalties, bar_width, color=colors[i], alpha=0.8,
                 label=f'{display_name} = {total_penalty:,})', edgecolor='black')

    plt.yticks(y_pos + bar_width, labels)
    plt.xlabel('Штрафные баллы', fontsize=12)

    plt.title(f'Нагрузка по каждому пальцу - {filename}',
              fontsize=16, fontweight='bold', pad=20)

    plt.legend(loc='upper right', fontsize=12, framealpha=0.9)

    plt.grid(axis='x', alpha=0.3, linestyle='--')

    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)

    plt.tick_params(axis='y', which='major', labelsize=11)
    plt.tick_params(axis='x', which='major', labelsize=10)

    plt.gca().invert_yaxis()

    all_vals = [pen for _, fp in all_results for pen in [fp[f] for f in finger_order]]
    max_penalty = max(all_vals) if all_vals else 1
    plt.xlim(0, max_penalty * 1.15)

    for i, (layout_name, finger_penalties) in enumerate(all_results):
        penalties = [finger_penalties[f] for f in finger_order]
        positions = y_pos + i * bar_width
        for pos, penalty in zip(positions, penalties):
            if penalty > 0:
                plt.text(penalty + max_penalty * 0.01, pos,
                         f'{penalty:,}', ha='left', va='center',
                         fontweight='bold', fontsize=9, color=colors[i])

    plt.tight_layout()
    plt.show()


def plot_hand_distribution(all_results, filename):
    """
    Строит круговые диаграммы распределения штрафов по рукам для каждой раскладки

    Args:
        all_results: список кортежей (название раскладки, штрафы по пальцам)
        filename: имя анализируемого файла

    Returns:
        None
    """
    fig, axes = plt.subplots(1, 3, figsize=(18, 7))

    layout_display_names = {
        'Йцукен': 'Йцукен',
        'Диктор': 'Диктор',
        'Вызов': 'Вызов'
    }

    for i, (layout_name, finger_penalties) in enumerate(all_results):
        left_penalty, right_penalty = calculate_hand_penalties(finger_penalties)
        total_penalty = left_penalty + right_penalty

        display_name = layout_display_names.get(layout_name, layout_name)

        sizes = [left_penalty, right_penalty]

        wedges, texts, autotexts = axes[i].pie(sizes, colors=['#ff6b6b', '#1f77b4'],
                                               autopct=lambda pct: f'{pct:.1f}%',
                                               startangle=90, textprops={'fontsize': 10, 'fontweight': 'bold'})

        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')

        axes[i].set_title(f'{display_name}\nОбщий штраф: {total_penalty:,}\n'
                          f'Левая: {left_penalty:,} | Правая: {right_penalty:,}',
                          fontsize=11, fontweight='bold', pad=10)

    plt.suptitle(f'Нагрузка по каждой руке - {filename}',
                 fontsize=16, fontweight='bold', y=0.97)
    plt.tight_layout()
    plt.subplots_adjust(top=0.85)
    plt.show()


def main():
    """
    Основная функция программы.
    Анализирует 3 заданных файла на трех раскладках клавиатуры: Йцукен, Диктор, Вызов.
    Выводит в консоль статистику по каждому файлу и раскладке, а также отображает 2 графика:
    первый - нагрузка на пальцы
    второй - нагрузка по рукам

    Returns:
        None
    """
    print("Анализатор нагрузки пальцев")
    print("=" * 50)

    layouts = [qwerty_layout(), dictor_layout(), vizov_layout()]
    files_to_analyze = ['digramms.txt', 'voina-i-mir.txt', '1grams-3.txt']

    for filename in files_to_analyze:
        if os.path.exists(filename):
            file_results = []

            for layout_config in layouts:
                print(f"\nАнализируем {filename} ({layout_config['name']})...")
                total_penalty, finger_penalties, total_chars = analyze_file(filename, layout_config)

                if total_chars > 0:
                    ru_finger_names = {
                        'f5l': 'Левый мизинец', 'f4l': 'Левый безымянный', 'f3l': 'Левый средний',
                        'f2l': 'Левый указательный', 'f1l': 'Левый большой', 'f1r': 'Правый большой',
                        'f2r': 'Правый указательный', 'f3r': 'Правый средний', 'f4r': 'Правый безымянный',
                        'f5r': 'Правый мизинец'
                    }

                    print("Штрафы по пальцам:")
                    for finger_code, finger_name in ru_finger_names.items():
                        penalty = finger_penalties[finger_code]
                        print(f"  {finger_name}: {penalty}")

                    left_penalty, right_penalty = calculate_hand_penalties(finger_penalties)
                    print(f"\nШтрафы по рукам:")
                    print(f"  Левая рука: {left_penalty}")
                    print(f"  Правая рука: {right_penalty}")

                    print(f"\nСуммарный штраф: {total_penalty}")
                    print(f"Всего символов: {total_chars}")

                    file_results.append((layout_config['name'], finger_penalties))
                else:
                    print("Файл пуст или ошибка чтения")
                print("=" * 50)

            if file_results:
                plot_finger_penalties_comparison(file_results, filename)
                plot_hand_distribution(file_results, filename)

        else:
            print(f"Файл {filename} не найден")


if __name__ == "__main__":
    main()