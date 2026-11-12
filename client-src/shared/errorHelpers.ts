/**
 * Groups messages by their name and counts how often each name occurs.
 * The name is the part of a message before the first separator (trimmed),
 * or the whole message if it contains no separator.
 *
 * @example
 * groupByMessageCount(["QRCodeError: not found", "QRCodeError: unreadable", "Timeout"]);
 * // Map { "QRCodeError" => 2, "Timeout" => 1 }
 *
 * @param messages - The messages to group, e.g. error messages like "ErrorName: details".
 * @param separator - Separates the name from the rest of the message. Defaults to ":".
 * @returns A Map from name to count, in order of first occurrence.
 */
export function groupByMessageCount(messages: string[], separator = ":") {
    const messageSummaryCount = new Map<string, number>();
    for (const message of messages) {
        const separatorIndex = message.indexOf(separator);
        const name = (separatorIndex === -1 ? message : message.slice(0, separatorIndex)).trim();
        messageSummaryCount.set(name, (messageSummaryCount.get(name) ?? 0) + 1);
    }
    return messageSummaryCount;
}
