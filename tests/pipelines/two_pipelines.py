# pipen_args used in two pipelines in one python session should raise an error

from pipen import Proc, Pipen


class Process(Proc):
    input = 'a'
    output = 'b:file:b.txt'
    input_data = [0]
    script = 'echo {{in.a}} > {{out.b}}'


class Pipeline1(Pipen):
    starts = Process


class Pipeline2(Pipen):
    starts = Process


if __name__ == '__main__':
    Pipeline1().run()
    Pipeline2().run()
