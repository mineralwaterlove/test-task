import sys
import time
import argparse
import requests

def check_host(host):
    if not host.startswith('http://') and not host.startswith('https://'):
        raise ValueError(f"Хост должен начинаться с http:// или https://: {host}")
    return host

def check_args(args):
    if args.count < 1:
        raise ValueError("Количество запросов должно быть больше 0")

    hosts = []

    if args.hosts:
        for host in args.hosts.split(','):
            host = host.strip()
            if host:
                hosts.append(check_host(host))

    elif args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                for line in f:
                    host = line.strip()
                    if host:
                        hosts.append(check_host(host))
        except FileNotFoundError:
            raise ValueError(f"Файл не найден: {args.file}")
        except:
            raise ValueError("Ошибка при чтении файла")

    if len(hosts) == 0:
        raise ValueError("Не указаны хосты для тестирования")

    return hosts

def show_results(stats):
    result = f"""
Host: {stats['host']}
Success: {stats['success']}
Failed: {stats['failed']}  
Errors: {stats['errors']}
Min: {stats['min_time'] * 1000:.2f} ms
Max: {stats['max_time'] * 1000:.2f} ms
Avg: {stats['avg_time'] * 1000:.2f} ms
"""
    return result

def test_server(host, count):
    results = {
        'host': host,
        'success': 0,
        'failed': 0,
        'errors': 0,
        'times': []
    }

    for i in range(count):
        try:
            start = time.time()
            response = requests.get(host, timeout=10)
            end = time.time()
            time_taken = end - start
            results['times'].append(time_taken)

            if response.status_code >= 400:
                results['failed'] += 1
            else:
                results['success'] += 1

        except requests.exceptions.Timeout:
            results['errors'] += 1
            print(f"Таймаут при запросе к {host}", file=sys.stderr)
        except requests.exceptions.ConnectionError:
            results['errors'] += 1
            print(f"Ошибка соединения с {host}", file=sys.stderr)
        except Exception as e:
            results['errors'] += 1
            print(f"Ошибка при запросе к {host}: {e}", file=sys.stderr)

    if results['times']:
        results['min_time'] = min(results['times'])
        results['max_time'] = max(results['times'])
        results['avg_time'] = sum(results['times']) / len(results['times'])
    else:
        results['min_time'] = 0
        results['max_time'] = 0
        results['avg_time'] = 0

    return results

def get_arguments():
    parser = argparse.ArgumentParser(description='Программа для тестирования серверов')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-H', '--hosts', help='Список сайтов через запятую, например: https://yandex.ru,https://google.com')
    group.add_argument('-F', '--file', help='Файл со списком сайтов, каждый на новой строке')
    parser.add_argument('-C', '--count', type=int, default=1, help='Сколько запросов сделать к каждому сайту')
    parser.add_argument('-O', '--output', help='Куда сохранить результаты, если не указано - показать на экране')

    return parser.parse_args()

def main():
    try:
        args = get_arguments()
        hosts_list = check_args(args)
        count = len(hosts_list)

        print(f"Тестируем {count} сервер{'а' if 2 <= count <= 4 else 'ов' if count >= 5 else ''}")

        all_results = []
        for host in hosts_list:
            print(f"Тестируем {host}...")
            result = test_server(host, args.count)
            all_results.append(result)

        output_text = ""
        for result in all_results:
            output_text += show_results(result) + "\n"

        if args.output:
            try:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(output_text)
                print(f"Результаты сохранены в: {args.output}")
            except:
                print("Не удалось сохранить в файл, вывожу на экран:")
                print(output_text)
        else:
            print(output_text)

    except ValueError as e:
        print(f"Ошибка: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nТестирование прервано")
        sys.exit(1)
    except Exception as e:
        print(f"Неизвестная ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()