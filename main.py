import os
import matplotlib.pyplot as plt
from layout import qwerty_layout, dictor_layout

left_hand = {'f5l', 'f4l', 'f3l', 'f2l', 'f1l'}
right_hand = {'f1r', 'f2r', 'f3r', 'f4r', 'f5r'}

def calculate_fines(pos1, pos2):
    """
    Вычисляем штраф пальца за перемещение между позициями

    :param pos1: прошлая позиция пальца
    :param pos2: текущая позиция пальца
    :return: штрафной балл
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
    обрабатывает обычные символ, пробелы, shift, enter
    :param text: текст для анализа
    :param layout_config: данные расладки
    :return: суммарный штраф, штрафы по каждому пальцу, общее количество обработанных символов
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
        if char == ' ':
            space_finger = 'f1l'
            current_positions[space_finger] = layout[' ']
            previous_finger = space_finger
            total_chars += 1

        elif char.isupper() or char in '!@"№;%:?*()_+':
            shift_finger = 'f5l'
            movement_penalty = calculate_fines(current_positions[shift_finger], layout['shift'])
            finger_penalties[shift_finger] += movement_penalty
            total_penalty += movement_penalty

            current_positions[shift_finger] = layout['shift']
            previous_finger = shift_finger
            total_chars += 2

        elif char == '\n':
            enter_finger = 'f5r'
            movement_penalty = calculate_fines(current_positions[enter_finger], layout['enter'])
            finger_penalties[enter_finger] += movement_penalty
            total_penalty += movement_penalty

            current_positions[enter_finger] = layout['enter']
            previous_finger = enter_finger
            total_chars += 1

        elif char in layout:
            current_pos = layout[char]
            finger = finger_assignment.get(char, 'f1l')

            movement_penalty = 0
            if current_positions[finger] != current_pos:
                movement_penalty = calculate_fines(
                    current_positions[finger], current_pos
                )

            change_hands = 0
            if previous_finger:
                current_hand = 'left' if finger in left_hand else 'right'
                previous_hand = 'left' if previous_finger in left_hand else 'right'
                if current_hand != previous_hand:
                    change_hands = 1

            total_char_penalty = movement_penalty + change_hands
            finger_penalties[finger] += total_char_penalty
            total_penalty += total_char_penalty

            current_positions[finger] = current_pos
            previous_finger = finger
            total_chars += 1

    return total_penalty, finger_penalties, total_chars


def analyze_file(filename, layout_config, chunk_size=1024 * 1024):
    """
    Анализ файлов
    :param filename: название файла
    :param layout_config: данные раскладки
    :param chunk_size: размер части для чтения больших файлов (1мб)
    :return: сумма штрафов, штраф по каждому пальцу, общее колво символов
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


def plot_finger_penalties(finger_stats, filename, layout_name):
    """
    Строим диаграмму штрафов по пальцам
    :param finger_stats: словарь со штрафами по пальцам
    :param filename: имя файла
    :param layout_name: название раскладки для заголовков графиков
    :return: None
    """
    finger_names = {
        'f5l': 'Левый\nмизинец',
        'f4l': 'Левый\nбезымянный',
        'f3l': 'Левый\nсредний',
        'f2l': 'Левый\nуказательный',
        'f1l': 'Левый\nбольшой',
        'f1r': 'Правый\nбольшой',
        'f2r': 'Правый\nуказательный',
        'f3r': 'Правый\nсредний',
        'f4r': 'Правый\nбезымянный',
        'f5r': 'Правый\nмизинец'
    }

    # Подготовка данных для графика
    fingers = list(finger_names.keys())
    labels = [finger_names[f] for f in fingers]
    penalties = [finger_stats[f] for f in fingers]
    total_penalty = sum(penalties)

    plt.figure(figsize=(12, 6))
    bars = plt.bar(labels, penalties, color = ['#ff6b6b', '#ffa726', '#ffee58', '#66bb6a', '#42a5f5',
              '#5c6bc0', '#ab47bc', '#ec407a', '#26c6da', '#26a69a'], edgecolor='black', alpha=0.8)

    for bar, penalty in zip(bars, penalties):
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(penalties) * 0.01,
                 f'{penalty}', ha='center', va='bottom', fontweight='bold')

    plt.title(f'Штрафы по пальцам\n{filename} ({layout_name})', fontsize=16, fontweight='bold')
    plt.xlabel('Пальцы')
    plt.ylabel('Штрафные баллы')
    plt.grid(axis='y', alpha=0.3)
    plt.xticks(rotation=45)

    if penalties:
        plt.ylim(0, max(penalties) * 1.15)

    plt.figtext(0.5, 0.01,
                f'Общий штраф: {total_penalty}',
                ha='center', bbox={'facecolor': 'lightgray', 'alpha': 0.7, 'pad': 5})

    plt.tight_layout()
    plt.subplots_adjust(bottom=0.15)
    plt.show()


def main():
    print("Анализатор нагрузки пальцев")
    print("=" * 50)

    layouts = [qwerty_layout(), dictor_layout()]
    files_to_analyze = ['digramms.txt', '1grams-3.txt', 'voina-i-mir.txt']

    for filename in files_to_analyze:
        if os.path.exists(filename):
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

                    print(f"Суммарный штраф: {total_penalty}")
                    print(f"Всего символов: {total_chars}")
                    plot_finger_penalties(finger_penalties, filename, layout_config['name'])
                else:
                    print("Файл пуст или ошибка чтения")
                print("=" * 50)
        else:
            print(f"Файл {filename} не найден")


if __name__ == "__main__":
    main()