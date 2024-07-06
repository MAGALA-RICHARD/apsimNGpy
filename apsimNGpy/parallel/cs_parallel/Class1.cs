using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using System.Linq;
using System.Diagnostics; // For Stopwatch

public static class ParallelHelper
{
    public static async Task<IEnumerable<TResult>> RunParallelAsync<T, TResult>(Func<T, TResult> func, IEnumerable<T> iterable, int? nCores = null, bool useThread = false, bool verbose = true)
    {
        int numberOfCores = nCores ?? Environment.ProcessorCount / 2;
        var options = new ParallelOptions { MaxDegreeOfParallelism = numberOfCores };

        List<TResult> results = new List<TResult>();
        Stopwatch stopwatch = Stopwatch.StartNew();

        if (verbose)
        {
            Console.WriteLine($"Processing via {func.Method.Name}, using {(useThread ? "threads" : "processes")}");
        }

        // Running the tasks in parallel
        await Task.Run(() =>
        {
            Parallel.ForEach(iterable, options, item =>
            {
                var result = func(item);
                lock (results) // Ensuring thread safety when adding to the list
                {
                    results.Add(result);
                }
            });
        });

        stopwatch.Stop();
        if (verbose)
        {
            Console.WriteLine($"Processed {results.Count} items took {stopwatch.Elapsed.TotalSeconds} seconds to run.");
            Console.WriteLine($"Efficiency per worker was: {(float)results.Count / numberOfCores}");
        }

        return results;
    }
}

// Usage Example:
// Assuming you have a function `ProcessItem` to be applied in parallel
public static int ProcessItem(int item)
{
    // Simulate some work
    Task.Delay(100).Wait();
    return item * item;
}

public static async Task Main(string[] args)
{
    var items = Enumerable.Range(1, 100);
    var results = await ParallelHelper.RunParallelAsync(ProcessItem, items, nCores: 4, useThread: false, verbose: true);

    foreach (var result in results)
    {
        Console.WriteLine(result);
    }
}
