#!/usr/bin/env python3
# ===============================================================================
# NAME: tinyseqgen
#
# DESCRIPTION: A tiny sequence generator for F Prime. This sequence compiler takes a
# .seq file as input and produces a binary sequence file compatible with the
# F Prime sequence file loader and sequence file runner.
# AUTHOR: Kevin Dinkel
# EMAIL:  dinkel@jpl.nasa.gov
# DATE CREATED: December 15, 2015
#
# Copyright 2015, California Institute of Technology.
# ALL RIGHTS RESERVED. U.S. Government Sponsorship acknowledged.
# ===============================================================================

import argparse
import os
from pathlib import Path
import sys

from fprime_gds.common.models.serialize.time_type import TimeType

from fprime_gds.common.data_types import exceptions as gseExceptions
from fprime_gds.common.data_types.cmd_data import CmdData, CommandArgumentsException
from fprime_gds.common.data_types.directive_data import DirectiveData
from fprime_gds.common.encoders.seq_writer import SeqBinaryWriter
from fprime_gds.common.loaders.cmd_json_loader import CmdJsonLoader
from fprime_gds.common.parsers.lark_seq_parser import LarkSeqFileParser
from fprime_gds.executables.cli import DictionaryParser, ParserBase
from typing import Any, Dict, Tuple

__author__ = "Tim Canham"
__version__ = "1.0"
__email__ = "timothy.canham@jpl.nasa.gov"


class SeqGenException(gseExceptions.GseControllerException):
    def __init__(self, val):
        super().__init__(str(val))


# except:
#  __error("The Gse source code was not found in your $PYTHONPATH variable. Please set PYTHONPATH to something like: $BUILD_ROOT/Gse/src:$BUILD_ROOT/Gse/generated/$DEPLOYMENT_NAME")


def generateSequence(inputFile, outputFile, dictionary, timebase, cont=False):
    """
    Write a binary sequence file from a text sequence file
    @param inputFile: A text input sequence file name (usually a .seq extension)
    @param outputFile: An output binary sequence file name (usually a .bin extension)
    """

    # Check for files
    if not os.path.isfile(inputFile):
        msg = f"Can't open file '{inputFile}'. "
        raise SeqGenException(msg)

    if not os.path.isfile(dictionary):
        msg = f"Can't open file '{dictionary}'. "
        raise SeqGenException(msg)

    # Check the user environment:
    cmd_json_dict = CmdJsonLoader(dictionary)
    try:
        (cmd_id_dict, cmd_name_dict, versions) = cmd_json_dict.construct_dicts(
            dictionary
        )
    except gseExceptions.GseControllerUndefinedFileException:
        msg = f"Can't open file '{dictionary}'. "
        raise SeqGenException(msg)

    # Parse the input file:
    sequence_list = []  # Can contain both CmdData and DirectiveData
    file_parser = LarkSeqFileParser()

    filename_abs = Path(inputFile).absolute()
    parsed_seq = file_parser.parse(inputFile, cont=cont)

    messages = []
    try:
        for i, descriptor, seconds, useconds, mnemonic_or_directive, args in parsed_seq:
            try:
                # Check if this is a directive
                if descriptor == "DIRECTIVE":
                    # This is a directive
                    directive_name = mnemonic_or_directive
                    try:
                        directive_data = DirectiveData(directive_name, args)
                        sequence_list.append(directive_data)
                    except ValueError as e:
                        msg = f"{filename_abs}:{i + 1}: {directive_name} errored: {str(e)}"
                        raise SeqGenException(msg) from e
                else:
                    # This is a command
                    mnemonic = mnemonic_or_directive
                    if mnemonic not in cmd_name_dict:
                        msg = f"{filename_abs}:{i + 1}: '{mnemonic}' does not match any command in the command dictionary."
                        raise SeqGenException(msg)
                    # Set the command arguments:
                    try:
                        cmd_time = TimeType(
                            TimeType.TimeBase("TB_DONT_CARE"),
                            seconds=seconds,
                            useconds=useconds,
                        )
                        cmd_data = CmdData(
                            args,
                            cmd_name_dict[mnemonic],
                            cmd_desc=descriptor,
                            cmd_time=cmd_time,
                        )
                    except CommandArgumentsException as e:
                        msg = f"{filename_abs}:{i + 1}: {mnemonic} errored: {','.join(e.errors)}"
                        raise SeqGenException(msg) from e
                    sequence_list.append(cmd_data)
            except SeqGenException as exc:
                if not cont:
                    raise exc
                messages.append(exc.getMsg())
    except gseExceptions.GseControllerParsingException as e:
        raise SeqGenException("\n".join([e.getMsg()] + messages))
    if cont and messages:
        raise SeqGenException("\n".join(messages))

    # Validate labels: collect all defined labels and referenced labels
    defined_labels = set()
    referenced_labels = set()

    for item in sequence_list:
        if isinstance(item, DirectiveData):
            if item.get_directive_name() == "LABEL":
                label_name = item.get_args()[0]
                if label_name in defined_labels:
                    msg = f"{filename_abs}: Duplicate label '{label_name}' found"
                    raise SeqGenException(msg)
                defined_labels.add(label_name)
            elif item.get_directive_name() in ("JCF", "JCS"):
                label_name = item.get_args()[0]
                referenced_labels.add(label_name)

    # Check that all referenced labels are defined
    undefined_labels = referenced_labels - defined_labels
    if undefined_labels:
        msg = f"{filename_abs}: Undefined labels referenced: {', '.join(sorted(undefined_labels))}"
        raise SeqGenException(msg)

    # Write to the output file:
    writer = SeqBinaryWriter(timebase=timebase)
    if not outputFile:
        outputFile = f"{os.path.splitext(inputFile)[0]}.bin"
    try:
        writer.open(outputFile)
    except OSError as exc:
        msg = f"Encountered problem opening output file '{outputFile}': {exc}"
        raise SeqGenException(msg) from exc

    writer.write(sequence_list)
    writer.close()


help_text = "seqgen.py -d"


class SeqGenParser(ParserBase):
    """Parser for deployments"""

    DESCRIPTION = "Seqgen options"

    def get_arguments(self) -> Dict[Tuple[str, ...], Dict[str, Any]]:
        """Arguments to handle deployments"""
        return {
            ("sequence",): {"help": "Path to input sequence file"},
            ("output",): {
                "nargs": "?",
                "help": "Path to output binary file",
                "default": None,
            },
            ("-t", "--timebase"): {
                "dest": "timebase",
                "help": "Set base path to generated command/telemetry definition files [default: any]",
                "default": None,
            },
        }

    def handle_arguments(self, args, **kwargs):
        """Handle arguments as parsed"""
        return args


def main():
    """
    The main program if run from the command line. Note that this file can also be used
    as a module by calling the generateSequence() function
    """

    # Parse and handle arguments, including SeqGen options and loading the dictionary into config
    args, _ = ParserBase.parse_args(
        [DictionaryParser, SeqGenParser],
        description="F prime SeqGen layer.",
        client=True,
    )

    if args.timebase is None:
        timebase = 0xFFFF
    else:
        try:
            timebase = int(args.timebase, 0)
        except ValueError:
            print(f"Could not parse time base {args.timebase}")
            return 1

    inputfile = args.sequence
    outputfile = args.output
    try:
        generateSequence(inputfile, outputfile, args.dictionary, timebase)
    except SeqGenException as e:
        print(e.getMsg())
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
